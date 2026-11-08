"""Read/hash-check frozen Nov2–8 source evidence. Never execute archived programs."""
from pathlib import Path
from collections.abc import Mapping
from functools import lru_cache
import argparse
import csv
import gzip
import hashlib
import io
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
INDEX = "provenance/week-source-index-20261108.json"
COVERAGE = "provenance/week-coverage-20261108.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe_path(name):
    path = (ROOT / name).resolve()
    require(path.is_relative_to(ROOT), "Source path escapes repository")
    return path


class RawObjects(Mapping):
    """A verified lazy object mapping; values are read with a bounded shard cache."""
    def __init__(self, evidence):
        self.evidence = evidence

    def __len__(self):
        return len(self.evidence.object_metadata)

    def __iter__(self):
        return iter(self.evidence.object_metadata)

    def __getitem__(self, h):
        meta = self.evidence.object_metadata[h]
        return self.evidence._read_object(h, meta["shards"], meta["bytes"])


class Evidence:
    def __init__(self):
        manifest = json.loads((ROOT / INDEX).read_text())
        self.rows = []
        names = set()
        for shard in manifest["shards"]:
            require(shard["path"] not in names, "Duplicate source-index shard")
            names.add(shard["path"])
            packed = safe_path(shard["path"]).read_bytes()
            require(len(packed) == shard["bytes"] and digest(packed) == shard["sha256"], "Source-index shard hash mismatch")
            decoded = gzip.decompress(packed)
            require(len(decoded) == shard["decoded_bytes"], "Source-index decoded size mismatch")
            reader = csv.DictReader(io.StringIO(decoded.decode("utf8"), newline=""))
            require(reader.fieldnames == manifest["columns"], "Source-index columns mismatch")
            rows = list(reader)
            require(len(rows) == shard["rows"], "Source-index shard row count mismatch")
            self.rows.extend(rows)
        require(len(self.rows) == manifest["source_entries"], "Source-index total count mismatch")
        self.index = {row["source_path"]: row for row in self.rows}
        require(len(self.index) == len(self.rows), "Duplicate indexed source path")
        self.coverage = json.loads((ROOT / COVERAGE).read_text())
        require(len(self.rows) == self.coverage["source_entries"], "Source index count mismatch")
        self.shards = {shard["path"]: shard for shard in self.coverage["shards"]}
        require(len(self.shards) == len(self.coverage["shards"]), "Repeated raw shard")
        self.objects = None
        self.object_metadata = None

    @lru_cache(maxsize=4)
    def _shard_records(self, name):
        shard = self.shards[name]
        packed = safe_path(name).read_bytes()
        require(len(packed) == shard["bytes"] and digest(packed) == shard["sha256"], "Raw shard hash mismatch")
        data = gzip.decompress(packed)
        require(len(data) == shard["decoded_bytes"], "Raw shard decoded size mismatch")
        return [json.loads(line) for line in data.splitlines()]

    def verify_objects(self):
        if self.object_metadata is not None:
            return {"state": "passed", "objects": len(self.object_metadata),
                    "original_bytes": sum(m["bytes"] for m in self.object_metadata.values())}
        metadata = {}
        current = None
        hasher = None
        size = 0
        next_part = 1
        declared_parts = 0
        declared_size = 0
        locations = []

        def finish():
            if current is not None:
                require(next_part == declared_parts + 1 and size == declared_size and hasher.hexdigest() == current,
                        "Reassembled raw object hash/size/parts mismatch")
                require(current not in metadata, "Repeated or noncontiguous raw object")
                metadata[current] = {"bytes": size, "shards": locations.copy()}

        for name in self.shards:
            for row in self._shard_records(name):
                h = row["sha256"]
                if h != current:
                    finish()
                    current = h
                    hasher = hashlib.sha256()
                    size = 0
                    next_part = 1
                    declared_parts, declared_size = row["parts"], row["bytes"]
                    locations = []
                require(row["part"] == next_part and row["parts"] == declared_parts and row["bytes"] == declared_size,
                        "Invalid raw fragment order/metadata")
                data = row["utf8"].encode("utf8")
                hasher.update(data)
                size += len(data)
                next_part += 1
                if name not in locations:
                    locations.append(name)
        finish()
        require(len(metadata) == self.coverage["raw_objects_in_included_shards"], "Raw corpus object count mismatch")
        self.object_metadata = metadata
        return {"state": "passed", "objects": len(metadata), "original_bytes": sum(m["bytes"] for m in metadata.values())}

    def _read_object(self, h, locations, expected_size):
        pieces = {}
        count = None
        for name in locations:
            for row in self._shard_records(name):
                if row["sha256"] != h:
                    continue
                require(row["part"] not in pieces, "Repeated requested object fragment")
                require(count is None or count == row["parts"], "Requested object fragment count mismatch")
                require(row["bytes"] == expected_size, "Requested object byte size mismatch")
                count = row["parts"]
                pieces[row["part"]] = row["utf8"]
        require(count is not None and set(pieces) == set(range(1, count + 1)), "Requested raw object is incomplete")
        data = "".join(pieces[i] for i in range(1, count + 1)).encode("utf8")
        require(len(data) == expected_size and digest(data) == h, "Requested raw object hash mismatch")
        return data

    def corpus(self):
        self.verify_objects()
        if self.objects is None:
            self.objects = RawObjects(self)
        return self.objects

    def read(self, source_path):
        row = self.index[source_path]
        kind = row["publication_kind"]
        if kind == "exact_file":
            data = safe_path(row["repository_path"]).read_bytes()
        elif kind == "lossless_text_object":
            data = self._read_object(row["sha256"], row["repository_path"].split(";"), int(row["bytes"]))
        else:
            raise ValueError("Not distributed as bytes: " + kind + "; " + row["reason"])
        require(len(data) == int(row["bytes"]) and digest(data) == row["sha256"], "Source bytes mismatch: " + source_path)
        return data

    def json(self, source_path):
        return json.loads(self.read(source_path))

    def table(self, source_path):
        return list(csv.DictReader(io.StringIO(self.read(source_path).decode("utf-8-sig"))))

    def verify_sources(self):
        self.verify_objects()
        unique = set()
        aliases = 0
        external = 0
        for row in self.rows:
            if row["publication_kind"] not in {"exact_file", "lossless_text_object"}:
                external += 1
                continue
            aliases += 1
            key = (row["sha256"], row["repository_path"])
            if key not in unique:
                if row["publication_kind"] == "lossless_text_object":
                    meta = self.object_metadata[row["sha256"]]
                    require(meta["bytes"] == int(row["bytes"])
                            and meta["shards"] == row["repository_path"].split(";"),
                            "Source-index raw object location/size mismatch")
                else:
                    self.read(row["source_path"])
                unique.add(key)
        return {"state": "passed", "source_paths_verified": aliases,
                "unique_content_locations_verified": len(unique), "external_paths": external,
                "raw_objects_verified": len(self.object_metadata), "new_experiments": 0, "new_model_requests": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?")
    parser.add_argument("--search", action="store_true")
    parser.add_argument("--verify-objects", action="store_true")
    parser.add_argument("--verify-sources", action="store_true")
    args = parser.parse_args()
    evidence = Evidence()
    if args.verify_sources:
        print(json.dumps(evidence.verify_sources(), ensure_ascii=False))
    elif args.verify_objects:
        print(json.dumps(evidence.verify_objects()))
    elif not args.query:
        parser.error("Provide a source path, --search query, --verify-objects or --verify-sources")
    elif args.search:
        for row in evidence.rows:
            if args.query in row["source_path"]:
                print(row["source_path"] + "\t" + row["publication_kind"] + "\t" + row["repository_path"])
    else:
        try:
            sys.stdout.buffer.write(evidence.read(args.query))
        except (KeyError, ValueError) as error:
            raise SystemExit(str(error))


if __name__ == "__main__":
    main()

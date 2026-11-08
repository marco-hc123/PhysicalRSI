# Experiment Result

## Material Passport
- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-11-02
- Verification Status: VERIFIED
- Version Label: system2_model_swap_v1

{
  "utc": "2026-11-02T03:10:14.943574+00:00",
  "status": "complete",
  "scope": "One model-swap System2 candidate, five paired validation layouts; no new feedback or manual code repair",
  "groups": [
    {
      "condition": "parent",
      "planned": 5,
      "attempted": 6,
      "completed": 5,
      "successes": 0,
      "mean_score": 0.0,
      "incomplete_attempts": 1,
      "unattempted": 0
    },
    {
      "condition": "gpt_candidate",
      "planned": 5,
      "attempted": 5,
      "completed": 5,
      "successes": 0,
      "mean_score": 0.0,
      "incomplete_attempts": 0,
      "unattempted": 0
    }
  ],
  "reference_groups": [
    {
      "condition": "qwen_parent",
      "episodes": 5,
      "successes": 0,
      "mean_score": 0.0
    },
    {
      "condition": "qwen_candidate",
      "episodes": 5,
      "successes": 0,
      "mean_score": 0.0
    }
  ],
  "selection": {
    "schema_version": 1,
    "comparison_sha256": "46bca3bbaed1ba928c81fa2bf0bebfcb15735e4379947805521cc2c0b57c8f6c",
    "cohort_sha256": "dadca87f5a6ad426aafb36c241f2c688b8627712d6e8b57fdd5b5f484e30de8f",
    "parent_id": "initial",
    "survivor_id": "initial",
    "survivor_freeze_sha256": "99d38502b2eefb89336747aa83e22c929605408bfb96da0d1a56257fc04244d4",
    "decision": "retain_parent",
    "metrics": {
      "candidate_round-000000": {
        "normalized_score": 0.0,
        "per_task": {
          "classify_objects": 0.0
        },
        "success_rate": {
          "classify_objects": 0.0
        }
      },
      "initial": {
        "normalized_score": 0.0,
        "per_task": {
          "classify_objects": 0.0
        },
        "success_rate": {
          "classify_objects": 0.0
        }
      }
    },
    "rejected": {
      "candidate_round-000000": {
        "reason": "no_sufficient_improvement",
        "normalized_gain": 0.0
      }
    },
    "result_sha256": {
      "candidate_round-000000": "ebadaa975860da9cd7de0791e92e91d704dd1097e3eee8d4e3cf61edb73a7be9",
      "initial": "3fd7d475e7d964615130bf5219b0ae7690e9def0eb51cc000c43164ea82104bb"
    },
    "scope": "native_robodojo; qualification requires native evidence"
  },
  "failure": null,
  "model_usage": {
    "completion_tokens": 2338,
    "completion_tokens_details": {
      "accepted_prediction_tokens": 0,
      "audio_tokens": 0,
      "reasoning_tokens": 512,
      "rejected_prediction_tokens": 0
    },
    "prompt_tokens": 3138,
    "prompt_tokens_details": {
      "audio_tokens": 0,
      "cache_write_tokens": 3135,
      "cached_tokens": 0
    },
    "total_tokens": 5476
  },
  "reference_model_usage": {
    "completion_tokens": 22532,
    "completion_tokens_details": {
      "reasoning_tokens": 21232,
      "text_tokens": 22532
    },
    "prompt_tokens": 3831,
    "prompt_tokens_details": {
      "cached_tokens": 0,
      "text_tokens": 3831
    },
    "total_tokens": 26363
  },
  "model_id": "gpt-6.1-sol",
  "provider_response_id": "chatcmpl-EfbvEGLe5u9T9jlphQm2CwLduASHB",
  "proposal_seconds": 33.85678264000012,
  "reference_proposal_seconds": 361.79368145400076,
  "gate_passed": true,
  "exact_original_prompt": true,
  "manual_candidate_edits": false,
  "development_native_reused": 10,
  "validation_native_completed": 10,
  "new_model_requests": 1,
  "infrastructure_interrupted_attempts": 1,
  "total_native_dispatch_attempts": 11,
  "recovered_after_power_loss": true,
  "independent_20_case_final_test_performed": false,
  "candidate_source_sha256": "339ddd5d8c4c3f7195e57f297ed99b2579da122f116baac7af365a3421dd1e08"
}

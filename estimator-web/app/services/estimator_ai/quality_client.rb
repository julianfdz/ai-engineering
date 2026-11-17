# Session 11 (local) — client for the generation-quality demos of the Calidad page.
# Thin wrappers over endpoints the IA service already exposes; no new contract:
#   POST /v1/estimate/stages/verify    → hallucination gate (anchor + optional judge)
#   POST /v1/estimate/tasks/hours      → per-task hours + range on contradiction
#   POST /v1/estimate/stages/retrieve  → the chunks the augmentation demo shapes
#   POST /v1/estimate/stages/assemble  → context block with/without augmentation
#   GET/PUT /api/v1/config/retrieval   → the S11 stage toggles (no restart)
module EstimatorAi
  class QualityClient < BaseClient
    def initialize(timeout: Rails.application.config.estimator_ai.timeout)
      super(
        timeout: timeout,
        default_headers: { "X-API-Key" => Rails.application.config.estimator_ai.estimate_api_key }
      )
    end

    def verify(estimate:, kept_chunks:, use_judge:)
      handle_response(json_conn.post("/v1/estimate/stages/verify", {
        estimate: estimate, kept_chunks: kept_chunks, use_judge: use_judge
      }))
    end

    def task_hours(modules:)
      handle_response(json_conn.post("/v1/estimate/tasks/hours", { modules: modules }))
    end

    def retrieve(query_text:, top_k: 8)
      handle_response(json_conn.post("/v1/estimate/stages/retrieve", {
        query_text: query_text, top_k: top_k, distance_threshold: 0.8
      }))
    end

    def assemble(chunks:, augment:)
      handle_response(json_conn.post("/v1/estimate/stages/assemble", {
        chunks: chunks, augment: augment, compress: true, reorder: true
      }))
    end

    def retrieval_config
      handle_response(json_conn.get("/api/v1/config/retrieval"))
    end

    # ``changes`` is a partial hash, e.g. { hallucination_gate_enabled: false };
    # nil resets a toggle to its .env default.
    def update_retrieval_config(changes)
      handle_response(json_conn.put("/api/v1/config/retrieval", changes))
    end
  end
end

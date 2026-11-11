# Context client for the Session 10 advanced retrieval endpoint
# (POST /v1/retrieval/advanced-search), guarded by the retrieval API key
# (X-API-Key header, injected once via BaseClient#default_headers).
module EstimatorAi
  class RetrievalClient < BaseClient
    def initialize(timeout: Rails.application.config.estimator_ai.timeout)
      super(
        timeout: timeout,
        default_headers: { "X-API-Key" => Rails.application.config.estimator_ai.retrieval_api_key }
      )
    end

    # ``params`` mirrors AdvancedRetrievalRequest: query_text, collections, top_k,
    # min_date, sectors, rerank, routing_enabled, query_transform_enabled,
    # temporal_decay_enabled. Nil values are dropped so the service applies its
    # own precedence (runtime override → .env default).
    def advanced_search(params)
      handle_response(json_conn.post("/v1/retrieval/advanced-search", params.compact))
    end
  end
end

# One run of the Session 10 advanced retrieval pipeline, launched from the
# «Búsqueda» view. Persists the request toggles and the full response so every
# decision (routing, technique, sub-queries, cardinality) can be revisited.
module Rag
  class AdvancedSearch < ApplicationRecord
    self.table_name = "advanced_searches"

    validates :query_text, presence: true

    def routing = response_payload["routing"] || {}
    def technique = response_payload["technique"]
    def subqueries = response_payload["subqueries"] || []
    def cardinality = response_payload["cardinality"] || {}
    def chunks = response_payload["chunks"] || []
    def low_confidence? = response_payload["low_confidence"] == true

    def duration_seconds
      duration_ms ? (duration_ms / 1000.0).round(1) : nil
    end
  end
end

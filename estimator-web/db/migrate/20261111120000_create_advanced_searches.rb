class CreateAdvancedSearches < ActiveRecord::Migration[8.0]
  def change
    create_table :advanced_searches do |t|
      t.text    :query_text,       null: false
      t.jsonb   :request_params,   null: false, default: {}   # toggles and filters sent to FastAPI
      t.jsonb   :response_payload, null: false, default: {}   # full AdvancedRetrievalResult
      t.integer :duration_ms                                  # wall-clock of the FastAPI call

      t.timestamps
    end
    add_index :advanced_searches, :created_at
  end
end

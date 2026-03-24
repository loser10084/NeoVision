## Frontend Chat Multi-Agent Requirements

The frontend AI chat is backed by four specialized agents:

1. `quality_assessment_agent`
   - Scope: quality review, QA checklist, confidence assessment, risk explanation, review priorities
2. `operation_assistant_agent`
   - Scope: product usage, workflow operations, troubleshooting, feature guidance
3. `imaging_analysis_agent`
   - Scope: uploaded image analysis, imaging interpretation support, contouring hints, uncertainty summary
4. `clinical_guideline_retrieval_agent`
   - Scope: guideline retrieval, consensus lookup, evidence summary, source-based clinical references

### Routing rules

- If the request includes an image, route to `imaging_analysis_agent`
- If the query is about QA, review, confidence, or quality risks, route to `quality_assessment_agent`
- If the query is about product usage or operation steps, route to `operation_assistant_agent`
- If the query is about guidelines, consensus, evidence, or retrieval, route to `clinical_guideline_retrieval_agent`
- If no strong intent is detected, default to `operation_assistant_agent`

### Safety rules

- All agents answer in Simplified Chinese
- All agents can use `rag_search` and `web_search` when needed
- Guideline and quality answers should be source-based whenever possible
- No agent may provide a final diagnosis, prescription, dose decision, or treatment decision

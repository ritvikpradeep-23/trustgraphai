"""TrustGraph's trained AI engines, plugged into app.services.ai_model.TrustGraphAI.

  scam_engine           the original 4-signal scam engine (ai/src/trustgraph, ai/models)
  text_detector         fine-tuned distilroberta for AI-written text (ai/models/text_detector)
  engines               loads them once, only if the AI packages and trained models are present

The AI-text packages (torch, transformers) are optional: pip install -r ai/requirements-ai.txt.
Without them, or without trained models, every AI check stays "unavailable" and no score is made up.
"""

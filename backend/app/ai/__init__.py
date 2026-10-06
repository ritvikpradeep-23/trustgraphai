"""TrustGraph's trained AI engines, plugged into app.services.ai_model.TrustGraphAI.

  efficientnet_wrapper  Google's EfficientNet-B0 from Hugging Face (public, no token)
  combined_model        your trained real/fake layer on top of it (models/efficientnet_head.pt)
  face_detector         largest face per frame (OpenCV)
  frame_extractor       frames spread over the whole video
  text_detector         fine-tuned distilroberta for AI-written text (models/text_detector)
  engines               loads them once, only if the AI packages and trained models are present

The AI packages (torch, transformers, OpenCV) are optional: pip install -r requirements-ai.txt.
Without them, or without trained models, every AI check stays "unavailable" and no score is made up.
"""

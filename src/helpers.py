import json

MODEL = "claude-haiku-5-5"

def fix_strings(value, schema):
    """Smaller models sometimes send an object or a list as JSON text. Turn it back."""
    kind = schema.get("type")
    if kind in ("object", "array") and isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return value
    if kind == "object" and isinstance(value, dict):
        for name, sub in schema.get("properties", {}).items():
            if name in value:
                value[name] = fix_strings(value[name], sub)
    if kind == "array" and isinstance(value, list):
        item_schema = schema.get("items", {})
        value = [fix_strings(v, item_schema) for v in value]
    return value


DIAGNOSIS_TOOL = {
    "name": "report_diagnosis",
    "description": "Judge the photo, then report what is visible and the possible causes.",
    "input_schema": {
        "type": "object",
        "properties": {
            "photo_quality": {
                "type": "object",
                "properties": {
                    "verdict": {"type": "string", "enum": ["good", "usable", "poor"]},
                    "problems": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "For example: blurry, dark, too far away, glare, cropped. Empty if none.",
                    },
                    "retake_tip": {
                        "type": "string",
                        "description": "One short instruction for a better photo. Empty if the verdict is good.",
                    },
                },
                "required": ["verdict", "problems", "retake_tip"],
            },
            "subject_kind": {"type": "string", "enum": ["plant", "product", "work", "unclear"]},
            "subject": {"type": "string",
                        "description": "2 to 5 words, for example tea plant, bag of rice, tiled floor. 'unknown' if you cannot tell."},
            "what_i_see": {"type": "array", "items": {"type": "string"}},
            "could_not_judge": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Details that matter but cannot be seen in this photo.",
            },
            "causes": {
                "type": "array",
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "likelihood": {"type": "string", "enum": ["high", "medium", "low"]},
                        "evidence": {"type": "string"},
                    },
                    "required": ["name", "likelihood", "evidence"],
                },
            },
            "to_tell_them_apart": {"type": "array", "items": {"type": "string"}},
            "actions": {
                "type": "object",
                "properties": {
                    "safe_now": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Cheap steps that are harmless whatever the cause is.",
                    },
                    "fix_later": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "for_cause": {"type": "string"},
                                "only_if": {"type": "string",
                                            "description": "What the person must confirm first."},
                                "what_to_get": {"type": "string",
                                                "description": "Type of product or part. No brands, no prices."},
                                "check_before": {"type": "string",
                                                 "description": "What to read or ask first. No doses."},
                            },
                            "required": ["for_cause", "only_if", "what_to_get", "check_before"],
                        },
                    },
                    "local_help": {"type": "string",
                                   "description": "Who nearby can confirm or help."},
                },
                "required": ["safe_now", "fix_later", "local_help"],
            },
        },
        "required": ["photo_quality", "subject_kind", "subject", "what_i_see",
                     "could_not_judge", "causes", "to_tell_them_apart", "actions"],
    },
}




RETAKE_TIPS = {
    "too small": "Use the original photo, not a forwarded or screenshot copy. Move closer to the problem.",
    "too dark": "Retake in bright daylight, not in deep shade or indoors. Do not use the flash.",
    "too blurry": "Hold the phone with both hands, tap the leaf on the screen to focus, then take the photo.",
}



INSTRUCTIONS = """You help people in Cameroon work out what is wrong from a photo. The photo shows one of three things:
- plant: a crop or other plant.
- product: something made or sold, such as food, goods, tools or equipment.
- work: something built, fixed or made by a worker, such as a wall, wiring, a weld or sewing.
The person has a phone and a nearby shop or workshop. They may not have much money.

Rules:
- First judge the photo itself. Is it sharp enough, bright enough and close enough, and does it show the problem clearly? Be strict. A person can retake a photo, but cannot undo a wrong diagnosis.
- Verdict good: a clear view of the problem. Verdict usable: you can see the problem but some detail is missing. Verdict poor: you cannot see the problem clearly.
- If the verdict is poor, give no causes. Give a retake tip instead.
- Decide what the photo shows. If it is none of the three, or you cannot tell, use unclear. Say what you can see and ask what the person wants checked.
- Describe only what you can clearly see. Never describe texture, tiny dots or colour shades that the photo is too dark, small or blurry to show. Put those things in could_not_judge.
- A photo cannot show what the standard should be. If the person has not said what they expected, say so in could_not_judge.
- For a plant, the causes are diseases, pests, weather stress or nutrient problems.
- For a product, the causes are damage, spoilage, wear, poor storage or a fault from making it. Never suggest tasting or smelling food to test it. If food may be spoiled, say not to eat it. Never say a product is fake from a photo. Say what a person could check.
- For work, the causes are poor materials, poor method, wear or misuse. If the fault could hurt someone, such as wiring, structure, gas or a weld that carries load, say so first and say to use a qualified person. Never give repair steps for live electrical or load-bearing work.
- If the verdict is usable, never use likelihood high. Do not suggest a cause because of one small clue.
- Otherwise give up to 3 possible causes, most likely first, each with a likelihood (high, medium or low) and the evidence in the photo.
- If two causes look alike in a photo, say so. Do not pick one just to sound sure.
- List what the person could check or photograph to tell the causes apart.
- Give actions in three groups. safe_now: cheap steps that are harmless whatever the cause turns out to be. fix_later: a fix for one cause, only after the person confirms it. local_help: who nearby can confirm the cause.
- Never put a step in safe_now that helps one cause but could hurt another.
- Never write a dose, a mixing amount, a repair measurement or a waiting period. Say to follow the label or ask the person who does the job.
- Name a type of product or part. Never a brand or a price.
- In fix_later, only_if must say what the person has to find out first. Never suggest a fix as the first step when two causes are still possible.
- In check_before, say what to read or ask first: the label and the waiting period before harvest for a crop treatment, the seller's return terms for a product, or the worker's guarantee for work.
- For local_help, name the kind of person: the nearest agriculture office or extension agent for plants, the seller or the consumer protection office for products, a qualified tradesperson for work. Do not invent names or phone numbers.
- Use short, plain sentences.
- Always give your answer by calling the report_diagnosis tool. Write nothing else."""



def media_type(raw):
    if raw.startswith(b"\x89PNG"):
        return "image/png"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


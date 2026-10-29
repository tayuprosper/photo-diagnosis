import base64
import sys
from pathlib import Path



from anthropic import Anthropic
from dotenv import load_dotenv
from src.quality import check
from src.helpers import DIAGNOSIS_TOOL, MODEL, INSTRUCTIONS, RETAKE_TIPS, media_type, fix_strings


load_dotenv()
client = Anthropic()



def diagnose(path, note=""):
    m, stops, warns = check(path)
    if stops:
        tip = " ".join(RETAKE_TIPS[p] for p in stops)
        return {"photo_quality": {"verdict": "poor", "problems": stops, "retake_tip": tip}}

    question = "What is wrong here? The photo may show a plant, a product or a piece of work."
    if note:
        question += " The person says: " + note
    if warns:
        question += (
            " A check on my computer found this photo is " + " and ".join(warns) + "."
            " Give a photo verdict of usable or poor, never good,"
            " and do not describe any detail you cannot clearly see."
        )

    raw = Path(path).read_bytes()

    data = base64.standard_b64encode(raw).decode()
    reply = client.messages.create(
        model=MODEL,
        max_tokens=2500,
        system=INSTRUCTIONS,
        tools=[DIAGNOSIS_TOOL],
        tool_choice={"type": "tool", "name": "report_diagnosis"},
        messages=[{
            "role": "user",
            "content": [
                {"type": "image",
                 "source": {"type": "base64", "media_type": media_type(raw), "data": data}},
                {"type": "text", "text": question},
            ],
        }],
    )

    if reply.stop_reason == "max_tokens":
        raise RuntimeError("The answer was cut off. Raise max_tokens.")
    block = next((b for b in reply.content if b.type == "tool_use"), None)
    if block is None:
        raise RuntimeError("No form came back from Claude.")
    result = block.input

    missing = [k for k in DIAGNOSIS_TOOL["input_schema"]["required"] if k not in result]
    if missing:
        raise RuntimeError("The answer is missing: " + ", ".join(missing))

   
    result = fix_strings(block.input, DIAGNOSIS_TOOL["input_schema"])
    for name in ("photo_quality", "actions"):
        if not isinstance(result.get(name), dict):
            raise RuntimeError(f"'{name}' came back as: {str(result.get(name))[:300]}")

    missing = [k for k in DIAGNOSIS_TOOL["input_schema"]["required"] if k not in result]
    if missing:
        raise RuntimeError("The answer is missing: " + ", ".join(missing))
    return result


def show(result):
    q = result["photo_quality"]
    print("Photo:", q["verdict"])
    for p in q["problems"]:
        print(" -", p)
    if q["verdict"] == "poor":
        print("\nRetake:", q["retake_tip"])
        return

    print(f"\nThis looks like: {result['subject']} ({result['subject_kind']})")
    print("\nWhat I see:")
    for line in result["what_i_see"]:
        print(" -", line)
    if result["could_not_judge"]:
        print("\nCould not judge from this photo:")
        for line in result["could_not_judge"]:
            print(" -", line)

    print("\nPossible causes:")
    for c in result["causes"]:
        print(f" [{c['likelihood']}] {c['name']}: {c['evidence']}")

    a = result["actions"]
    print("\nDo this now (safe whatever the cause):")
    for line in a["safe_now"]:
        print(" -", line)

    print("\nTo tell them apart:")
    for line in result["to_tell_them_apart"]:
        print(" -", line)

    for t in a["fix_later"]:
        print(f" - For: {t['for_cause']}")
        print(f"   Only if: {t['only_if']}")
        print(f"   Ask for: {t['what_to_get']}")
        print(f"   Check first: {t['check_before']}")
        
        
    print("\nGet help:", a["local_help"])
    if q["retake_tip"]:
        print("\nFor a better photo:", q["retake_tip"])


if __name__ == "__main__":
    show(diagnose(sys.argv[2], " ".join(sys.argv[2])))


from flask import Flask, render_template, request, jsonify
import json
import unicodedata
def normalize_text(text):
    """
    Normalize text for reliable keyword matching.

    Converts accented characters into their base characters
    while preserving the original text for display.
    """

    if not text:
        return ""

    normalized = unicodedata.normalize(
        "NFKD",
        text
    )

    return "".join(
        char
        for char in normalized
        if not unicodedata.combining(char)
    ).lower()
import re
import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# OpenAI client
api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    client = OpenAI(api_key=api_key)
    print("[STAGE 6B] OPENAI CLIENT: available")
else:
    client = None
    print("[STAGE 6B] OPENAI CLIENT: unavailable - local mode only")

# Load the government information knowledge base
with open("data/government_services.json", "r", encoding="utf-8") as file:
    services = json.load(file)


def find_service_by_keyword(question):
   
    """
    Find the best verified government service using intent-aware
    and scored keyword matching.

    Important:
    Do not return the first keyword match.
    Multiple services can share keywords such as "registu negósiu".
    """

    verified_services = [
        s for s in services
        if s.get("status") == "verified"
    ]

    question_lower = normalize_text(
    question
).strip()

    # ---------------------------------------------------------
    # 1. HIGH-PRIORITY INTENT RULES
    # ---------------------------------------------------------
    # These rules handle situations where a generic keyword
    # overlaps with a more specific service.
    #
    # Example:
    # "muda dadus iha registu negósiu"
    #
    # contains "registu negósiu", but the actual intention is
    # changing business information.
    # ---------------------------------------------------------

    intent_rules = [
        # -----------------------------------------------------
        # Business data / information changes
        # -----------------------------------------------------
        (
            [
                r"\bmuda\s+dadus\b",
                r"\bmuda\s+informasaun\b",
                r"\btroka\s+dadus\b",
                r"\btroka\s+informasaun\b",
                r"\baltera(?:saun)?\s+dadus\b",
                r"\baltera(?:saun)?\s+informasaun\b",
                r"\batualiza(?:saun)?\s+dadus\b",
                r"\batualiza(?:saun)?\s+informasaun\b",
                r"\bhadia\s+dadus\b",
                r"\bhadia\s+informasaun\b",
                r"\bkorrije\s+dadus\b",
                r"\bkorrije\s+informasaun\b",
                r"\bkoreje\s+dadus\b",
                r"\bkoreje\s+informasaun\b",
            ],
            "service_016"
        ),

        # -----------------------------------------------------
        # Business address changes
        # -----------------------------------------------------
        (
            [
                r"\bmuda\s+enderesu\b",
                r"\btroka\s+enderesu\b",
                r"\baltera\s+enderesu\b",
                r"\batualiza\s+enderesu\b",
            ],
            "service_016"
        ),

        # -----------------------------------------------------
        # Business authorization / license renewal
        # -----------------------------------------------------
        (
            [
                r"\brenova(?:r)?\b.*\bautorizasaun\b",
                r"\brenova(?:r)?\b.*\blisensa\b",
                r"\brenovasaun\b.*\bautorizasaun\b",
                r"\brenovasaun\b.*\batividade\b",
                r"\brenovasaun\b.*\blisensa\b",
                r"\brenova\s+lisensa\b",
                r"\brenovar\s+lisensa\b",
                r"\brenova\s+autorizasaun\b",
                r"\brenovar\s+autorizasaun\b",
                r"\brenova\s+atividade\b",
                r"\brenovar\s+atividade\b",
                r"\blisensa\s+presiza\s+renova\b",
                r"\blisensa\s+presiza\s+renovasaun\b",
                r"\bautorizasaun\s+presiza\s+renova\b",
                r"\bautorizasaun\s+presiza\s+renovasaun\b",
                r"\brenew\s+business\s+license\b",
                r"\bbusiness\s+license\s+renewal\b",
            ],
            "service_015"
        ),

        # -----------------------------------------------------
        # Marriage certificate
        # -----------------------------------------------------
        (
            [
                r"\bcertidaun\s+casamentu\b",
                r"\bcertidaun\s+kazamentu\b",
            ],
            "service_008"
        ),

        # -----------------------------------------------------
        # Death certificate / guide
        # -----------------------------------------------------
        (
            [
                r"\bguia\s+de\s+óbito\b",
                r"\bguia\s+de\s+obito\b",
                r"\bguia\s+obito\b",
                r"\bguia\s+óbito\b",
                r"\btrata\s+óbito\b",
                r"\btrata\s+obito\b",
                r"\btrata\s+guia\s+de\s+óbito\b",
                r"\btrata\s+guia\s+de\s+obito\b",
                r"\bhalo\s+guia\s+de\s+óbito\b",
                r"\bhalo\s+guia\s+de\s+obito\b",
                r"\bpresiza\s+guia\s+de\s+óbito\b",
                r"\bpresiza\s+guia\s+de\s+obito\b",
                r"\brejistu\s+obito\b",
                r"\bregistu\s+obito\b",
                r"\bcertidaun\s+obito\b",
                r"\bcertidaun\s+mate\b",
                r"\bprosesu\s+óbito\b",
                r"\bprosesu\s+obito\b",
            ],
            "service_005"
        ),

        # -----------------------------------------------------
        # Vehicle registration
        # -----------------------------------------------------
        (
            [
                r"\bregistu\s+automóvel\b",
                r"\bregistu\s+automovel\b",
                r"\brejistu\s+automóvel\b",
                r"\brejistu\s+automovel\b",
                r"\bregista(?:r)?\b.*\bautomóvel\b",
                r"\bregista(?:r)?\b.*\bautomovel\b",
                r"\brejista(?:r)?\b.*\bautomóvel\b",
                r"\brejista(?:r)?\b.*\bautomovel\b",
                r"\bhalo\s+registu\b.*\bautomóvel\b",
                r"\bhalo\s+registu\b.*\bautomovel\b",
                r"\bhalo\s+rejistu\b.*\bautomóvel\b",
                r"\bhalo\s+rejistu\b.*\bautomovel\b",
                r"\bregistu\s+kareta\b",
                r"\brejistu\s+kareta\b",
                r"\bregista(?:r)?\b.*\bkareta\b",
                r"\brejista(?:r)?\b.*\bkareta\b",
                r"\bhalo\s+registu\b.*\bkareta\b",
                r"\bhalo\s+rejistu\b.*\bkareta\b",
                r"\bregistu\s+motorizada\b",
                r"\brejistu\s+motorizada\b",
                r"\bregista(?:r)?\b.*\bmotorizada\b",
                r"\brejista(?:r)?\b.*\bmotorizada\b",
                r"\bregistu\s+motor\b",
                r"\brejistu\s+motor\b",
                r"\bregista(?:r)?\b.*\bmotor\b",
                r"\brejista(?:r)?\b.*\bmotor\b",
            ],
            "service_012"
        ),

          # -----------------------------------------------------
        # New business registration
        # -----------------------------------------------------
        (
            [
                r"\bregistu\s+negósiu\b",
                r"\bregistu\s+negosiu\b",
                r"\brejistu\s+negósiu\b",
                r"\brejistu\s+negosiu\b",
                r"\bregista(?:r)?\b.*\bnegósiu\b",
                r"\bregista(?:r)?\b.*\bnegosiu\b",
                r"\brejista(?:r)?\b.*\bnegósiu\b",
                r"\brejista(?:r)?\b.*\bnegosiu\b",
                r"\bhalo\s+registu\b.*\bnegósiu\b",
                r"\bhalo\s+registu\b.*\bnegosiu\b",
                r"\bkria\s+negósiu\b",
                r"\bkria\s+negosiu\b",
            ],
            "service_001"
        ),

        # -----------------------------------------------------
        # Marriage registration
        # -----------------------------------------------------
        (
            [
                r"\bregistu\s+kazamentu\b",
                r"\brejistu\s+kazamentu\b",
                r"\bregisto\s+casamento\b",
                r"\brejistu\s+casamento\b",
                r"\bhalo\s+registu\b.*\bkazamentu\b",
                r"\bhalo\s+registu\b.*\bcasamento\b",
                r"\bhalo\s+kazamentu\b",
                r"\bhalo\s+casamento\b",
                r"\bkaben\s+malu\b",
                r"\bhakarak\s+halo\s+kazamentu\b",
                r"\bhakarak\s+halo\s+casamento\b",
                r"\bhakarak\s+rejista\s+kazamentu\b",
                r"\bhakarak\s+rejista\s+casamento\b",
                r"\bpresiza\s+rejista\s+kazamentu\b",
                r"\bpresiza\s+rejista\s+casamento\b",
                r"\bpresiza\s+registu\s+kazamentu\b",
                r"\bpresiza\s+registu\s+casamento\b",
                r"\bcasal\s+presiza\s+rejista\b",
                r"\bcasal\s+presiza\s+registu\b",
            ],
            "service_007"
        ),
    ]

    # Apply high-priority intent rules.
    for patterns, service_id in intent_rules:
        for pattern in patterns:
            if re.search(
                normalize_text(pattern),
                question_lower
            ):
                for service in verified_services:
                    if service.get("id") == service_id:
                        return service

    # ---------------------------------------------------------
    # 2. NORMAL SCORED KEYWORD MATCHING
    # ---------------------------------------------------------

    scored_matches = []

    for service in verified_services:

        service_score = 0
        matched_keywords = []

        keywords = service.get("keywords", [])

        for keyword in keywords:

            if not keyword:
                continue

            keyword_lower = normalize_text(
    keyword
).strip()

            pattern = (
                r"(?<!\w)"
                + re.escape(keyword_lower)
                + r"(?!\w)"
            )

            if re.search(
    normalize_text(pattern),
    question_lower
):

                matched_keywords.append(keyword)

                # More specific phrases receive more points.
                word_count = len(keyword_lower.split())
                character_count = len(keyword_lower)

                if word_count >= 3:
                    points = 35
                elif word_count == 2:
                    points = 25
                else:
                    points = 10

                # Longer phrases are generally more specific.
                points += min(character_count // 5, 10)

                service_score += points

        # Bonus for multiple matching keywords.
        if len(matched_keywords) >= 2:
            service_score += 20

        if len(matched_keywords) >= 3:
            service_score += 20

        if service_score > 0:
            scored_matches.append(
                (
                    service_score,
                    service,
                    matched_keywords
                )
            )

    # ---------------------------------------------------------
    # 3. SELECT STRONGEST MATCH
    # ---------------------------------------------------------

    if not scored_matches:
        return None

    scored_matches.sort(
        key=lambda item: item[0],
        reverse=True
    )

    best_score, best_service, matched_keywords = scored_matches[0]

# ---------------------------------------------------------
# 4. LOCAL MATCH CONFIDENCE THRESHOLD
# ---------------------------------------------------------

    LOCAL_MATCH_THRESHOLD = 25

    if best_score < LOCAL_MATCH_THRESHOLD:
        return None

    return best_service


def identify_service_with_ai(question):
    """
    Use OpenAI only when local keyword matching does not
    identify the service.

    The AI is restricted to verified services in the
    local government knowledge base.
    """

    verified_services = [
        service for service in services
        if service.get("status") == "verified"
    ]

    if not verified_services:
        return None

    # --------------------------------------------------
    # Build a compact service list
    # --------------------------------------------------

    service_list = []

    for service in verified_services:
        service_list.append({
            "id": service.get("id"),
            "service": service.get("service"),
            "tetum_name": service.get("tetum_name"),
            "category": service.get("category")
        })

    # --------------------------------------------------
    # Compact classification prompt
    # --------------------------------------------------

    prompt = f"""
You are the intent-classification component of TETUM-AI.

TETUM-AI is a government information assistant for
Timor-Leste.

Identify the ONE verified government service that best
matches the user's question.

USER QUESTION:
{question}

VERIFIED SERVICES:
{json.dumps(service_list, ensure_ascii=False)}

RULES:

 1. Return ONLY one service ID or NONE.
 2. The ID must exactly match an ID in the verified services list.
 3. Never invent an ID.
 4. Understand the meaning and intent of the Tetum question.
 5. Do not answer the question.
 6. Do not provide explanations.
 7. If none of the services reasonably matches the question,
     return NONE.
 8. If the question is too vague to identify a specific service,
     return NONE.
 9. If two or more services could reasonably match and the
     question does not provide enough information to distinguish
     them, return NONE.
 10. A single general word or life event is NOT enough to identify
      a government service. For example, words such as "mate",
      "familia", "negósiu", "lisensa", or similar general terms
      must not by themselves determine the service.
 11. For a service to be selected, the question must express a
      clear intention to obtain, register, renew, change, apply
      for, or receive information about that specific service.
 12. Prefer NONE over making an uncertain guess.

 RETURN ONLY ONE OF:
 a verified service ID
 NONE
"""

    try:
        response = client.responses.create(
            model="gpt-5.6-luna",
            input=prompt
        )

        result = response.output_text.strip()

        # --------------------------------------------------
        # Security check:
        # AI can only return an ID from the verified database
        # --------------------------------------------------

        valid_ids = {
            service.get("id")
            for service in verified_services
        }

        if result not in valid_ids:
            return None

        for service in verified_services:
            if service.get("id") == result:
                return service

    except Exception as error:
        print("AI classification error:", error)

    return None

def create_local_tetum_answer(question, service):
    """
    Return a verified local Tetum answer without calling OpenAI.
    Detects specific information requests locally.
    """

    if not service:
        return (
            "Deskulpa, hau seidauk hetan informasaun "
            "kona-ba pergunta ne'e iha TETUM-AI."
        )

    question_lower = normalize_text(question).strip()

    # --------------------------------------------------
    # DOCUMENT REQUEST
    # --------------------------------------------------

    document_keywords = [
        "dokumentu saida",
        "dokuméntu saida",
        "documentu saida",
        "dokumenti saida",
        "presiza dokumentu saida",
        "presiza dokuméntu saida",
        "presiza documentu saida",
        "presiza dokumenti saida",
        "dokumentu nebee",
        "dokumentu nebe",
        "dokumentu ne'ebé",
        "dokumentu ne'ebe",
        "dokuméntu ne'ebé",
        "dokuméntu ne'ebe",
        "documentu nebe",
        "documentu ne'ebé",
        "documentu ne'ebe",
        "saidasa dokumentu",
        "saidasa dokuméntu",
        "documentos necessarios",
        "dokumentu nesesariu",
        "dokumentu sira ne'ebé presiza"
    ]

    if any(keyword in question_lower for keyword in document_keywords):

        documents = service.get("documents", [])

        if documents:
            return "Dokumentu ne'ebé presiza:\n" + "\n".join(
                f"- {document}" for document in documents
            )

        return (
            "Deskulpa, informasaun kona-ba dokumentu "
            "seidauk disponivel iha baze-dadus verifikadu TETUM-AI."
        )

    # --------------------------------------------------
    # PROCEDURE REQUEST
    # --------------------------------------------------

    procedure_keywords = [
        "prosedimentu",
        "procedimentu",
        "prosedimentu sira",
        "procedimentu sira",
        "etapa sira",
        "etapa ba",
        "etapa atu",
        "pasu sira",
        "pasu ba",
        "pasu atu",
        "dalan atu halo",
        "dalan atu rejista",
        "dalan atu hetan",
        "how to",
        "procedure",
        "procedures"
    ]

    if any(keyword in question_lower for keyword in procedure_keywords):

        procedure = service.get("procedure", [])

        if procedure:
            return "Prosedimentu:\n" + "\n".join(
                f"- {step}" for step in procedure
            )

        return (
            "Deskulpa, informasaun kona-ba prosedimentu "
            "seidauk disponivel iha baze-dadus verifikadu TETUM-AI."
        )

    # --------------------------------------------------
    # LOCATION REQUEST
    # --------------------------------------------------

    location_keywords = [
        "iha nebee",
        "iha nebe",
        "iha ne'ebé",
        "iha ne'ebe",
        "iha ne'e be",
        "enderesu",
        "endereco",
        "fatin nebee",
        "fatin nebe",
        "fatin ne'ebé",
        "fatin ne'ebe",
        "iha fatin nebee",
        "iha fatin nebe",
        "iha fatin ne'ebé",
        "iha fatin ne'ebe",
        "onde",
        "where"
    ]

    if any(keyword in question_lower for keyword in location_keywords):

        location = service.get("location")

        if location:
            return f"Fatin: {location}"

        return (
            "Deskulpa, informasaun kona-ba fatin "
            "seidauk disponivel iha baze-dadus verifikadu TETUM-AI."
        )

    # --------------------------------------------------
    # FEE REQUEST
    # --------------------------------------------------

    fee_keywords = [
        "taxa",
        "taxa hira",
        "osan hira",
        "folin hira",
        "custa hira",
        "custu hira",
        "quanto custa",
        "quanto custa",
        "quanto osan",
        "quanto selu",
        "selu hira",
        "presiza selu",
        "presiza osan",
        "folin servisu",
        "taxa servisu",
        "taxa rejistu",
        "gratis",
        "gratuitu",
        "fee"
        
    ]

    if any(keyword in question_lower for keyword in fee_keywords):

        fee = service.get("fee")

        if fee:
            return f"Taxa/Osan: {fee}"

        return (
            "Deskulpa, informasaun kona-ba taxa "
            "seidauk disponivel iha baze-dadus verifikadu TETUM-AI."
        )

    # --------------------------------------------------
    # PROCESSING TIME REQUEST
    # --------------------------------------------------

    processing_keywords = [
        "quanto tempu",
        "durasaun",
        "loron hira",
        "oras hira",
        "tempo hira",
        "tempu prosesamentu",
        "tempo prosesamentu",
        "durasaun prosesu",
        "durasaun prosesamentu",
        "loron hira",
        "oras hira",
        "tempu hira",
        "quanto tempo",
        "processing time"
    ]

    if any(keyword in question_lower for keyword in processing_keywords):

        processing_time = service.get("processing_time")

        if processing_time:
            return f"Tempu prosesamentu: {processing_time}"

        return (
            "Deskulpa, informasaun kona-ba tempu prosesamentu "
            "seidauk disponivel iha baze-dadus verifikadu TETUM-AI."
        )

    # --------------------------------------------------
    # GENERAL SERVICE QUESTION
    # --------------------------------------------------

    return service.get(
        "answer_tetum",
        "Deskulpa, hau seidauk hetan informasaun kona-ba servisu ne'e."
    )

def create_tetum_answer(question, service):
    """
    Generate a natural Tetum response using ONLY the
    verified information stored in the local database.
    """

    if not service:
        return (
            "Deskulpa, hau seidauk hetan informasaun "
            "kona-ba pergunta ne'e iha TETUM-AI."
        )

    # --------------------------------------------------
    # Build a minimal verified answer dataset.
    # Only information needed for citizen answers is sent
    # to the AI.
    # --------------------------------------------------

    verified_answer_data = {
        "service": service.get("service"),
        "tetum_name": service.get("tetum_name"),
        "answer_tetum": service.get("answer_tetum"),
        "documents": service.get("documents", []),
        "procedure": service.get("procedure", []),
        "location": service.get("location"),
        "fee": service.get("fee"),
        "processing_time": service.get("processing_time")
    }

    service_data = json.dumps(
        verified_answer_data,
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
You are TETUM-AI, a Tetum-first government information
assistant for Timor-Leste.

Answer the user's question in clear, simple and natural Tetum.

USER QUESTION:
{question}

VERIFIED GOVERNMENT SERVICE INFORMATION:
{service_data}

Rules:

1. Use ONLY the information contained in the verified
   government service information above.

2. Do not invent, assume, or infer government information.

3. Do not invent documents, fees, processing times,
   locations, telephone numbers, procedures, requirements,
   dates, durations, eligibility conditions, exceptions,
   or government policies.

4. Do not use general knowledge to fill missing
   government information.

5. Match the answer to the user's actual question.

6. If the user asks for one specific piece of information,
   answer that request first and focus primarily on it.

7. If the user asks specifically for documents, provide
   ONLY documents explicitly contained in the verified
   government service information.

8. If the user asks specifically about procedure, provide
   ONLY the relevant verified procedure information.

9. If the user asks specifically about location, provide
   ONLY the verified location.

10. If the user asks specifically about a fee, provide
    ONLY the verified fee information.

11. If the user asks specifically about processing time,
    provide ONLY the verified processing-time information.

12. If the requested information is missing from the
    verified database, clearly say that the current
    TETUM-AI database does not contain that information.

13. Do not create numerical durations unless the exact
    information is explicitly present in the verified
    database.

14. Do not add documents or requirements simply because
    they may normally apply to a government service.

15. Do not add statements such as "requirements may vary",
    "additional documents may be required", or similar
    statements unless explicitly contained in the verified
    information.

16. Do not add unrelated information.

17. Do not repeat the complete Documents, Procedure,
    Location, Fee, or Processing Time information when
    the user did not ask for those details.

18. Keep the answer concise and easy for ordinary citizens
    to understand.

19. Do not use Markdown formatting such as bold, italic,
    headings, bullet symbols, or code blocks.

20. Return clean plain text suitable for direct display
    in the TETUM-AI application.

21. Write the answer in natural Tetum.

"""

    try:
        response = client.responses.create(
            model="gpt-5.6-luna",
            input=prompt
        )

        return response.output_text.strip()

    except Exception as error:
        print("AI answer error:", error)

        # Safe fallback to the verified local answer
        return service.get(
            "answer_tetum",
            "Deskulpa, hau seidauk bele produz resposta."
        )

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    request_start = time.perf_counter()

    data = request.get_json()

    question = data.get(
        "question",
        ""
    ).strip()

    if not question:
        return jsonify({
            "answer": "Favor hakerek pergunta ida.",
            "documents": [],
            "procedure": [],
            "location": "",
            "fee": "",
            "processing_time": "",
            "source": "",
            "source_url": "",
            "service": ""
        })

    # --------------------------------------------------
    # STEP 1: Local verified keyword matching
    # --------------------------------------------------

    local_start = time.perf_counter()

    local_match = find_service_by_keyword(question)

    local_elapsed = time.perf_counter() - local_start

    service = local_match

    if local_match is not None:
        print(
            f"[STAGE 6C] LOCAL MATCH: "
            f"{local_match.get('id')} "
            f"({local_elapsed:.4f}s)"
        )
    else:
        print(
            f"[STAGE 6C] LOCAL MATCH: NONE "
            f"({local_elapsed:.4f}s)"
        )

    # --------------------------------------------------
    # STEP 2: AI intent classification if no local match
    # --------------------------------------------------

    if service is None:
        ai_classification_start = time.perf_counter()

        service = identify_service_with_ai(question)

        ai_classification_elapsed = (
            time.perf_counter() - ai_classification_start
        )

        print(
            f"[STAGE 6C] AI CLASSIFICATION: "
            f"{ai_classification_elapsed:.4f}s"
        )

    # --------------------------------------------------
    # STEP 3: No verified service found
    # --------------------------------------------------

    if service is None:
        total_elapsed = time.perf_counter() - request_start

        print(
            f"[STAGE 6C] TOTAL REQUEST: "
            f"{total_elapsed:.4f}s"
        )

        return jsonify({
            "answer": (
                "Deskulpa, hau seidauk hetan informasaun "
                "verifikadu kona-ba pergunta ne'e iha "
                "TETUM-AI."
            ),
            "documents": [],
            "procedure": [],
            "location": "",
            "fee": "",
            "processing_time": "",
            "source": "TETUM-AI Knowledge Base",
            "source_url": "",
            "service": ""
        })

    # --------------------------------------------------
    # STEP 4: Generate Tetum answer
    # --------------------------------------------------
  
    answer_start = time.perf_counter()

    answer = create_local_tetum_answer(question, service)

    answer_elapsed = time.perf_counter() - answer_start

    print(
        f"[STAGE 6C] LOCAL ANSWER: "
        f"{answer_elapsed:.4f}s"
    )

    # --------------------------------------------------
    # STEP 5: Total request timing
    # --------------------------------------------------

    total_elapsed = time.perf_counter() - request_start

    print(
        f"[STAGE 6C] TOTAL REQUEST: "
        f"{total_elapsed:.4f}s"
    )

    # --------------------------------------------------
    # STEP 6: Return verified service information
    # --------------------------------------------------

    return jsonify({
        "answer": answer,
        "documents": service.get(
            "documents",
            []
        ),
        "procedure": service.get(
            "procedure",
            []
        ),
        "location": service.get(
            "location",
            ""
        ),
        "fee": service.get(
            "fee",
            ""
        ),
        "processing_time": service.get(
            "processing_time",
            ""
        ),
          
        "last_verified": service.get(
            "last_verified",
            ""
        ),
        "source": service.get(
            "source_name",
            ""
        ),
        "source_url": service.get(
            "source_url",
            ""
        ),
        "service": service.get(
            "tetum_name",
            service.get("service", "")
        )
    })


if __name__ == "__main__":
    app.run(debug=True)





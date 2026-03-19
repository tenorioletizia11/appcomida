from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
DB_PATH = BASE_DIR / "data" / "appcomida.db"
USER_ID = 1


def load_env_file() -> None:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'").strip('"'))


SEED_DISHES = [
    {
        "name": "Bowl de pollo teriyaki",
        "mode": "cook",
        "cuisine": "Asiática",
        "cook_time": 20,
        "price_level": 2,
        "energy": "media",
        "tags": ["proteína", "rápido", "weekday", "comfort"],
        "description": "Un plato equilibrado, sabroso y fácil para noches ocupadas.",
        "ingredients": [
            ["Pechuga de pollo", "400 g"],
            ["Arroz jazmín", "1 taza"],
            ["Brócoli", "1 cabeza"],
            ["Salsa de soya", "3 cucharadas"],
            ["Miel", "1 cucharada"],
            ["Ajo", "2 dientes"],
        ],
        "steps": [
            "Cuece el arroz según el paquete.",
            "Corta el pollo en cubos y dóralo con ajo picado.",
            "Mezcla salsa de soya con miel y añade al pollo.",
            "Saltea el brócoli 4 minutos y sirve todo en un bowl.",
        ],
    },
    {
        "name": "Tacos de salmón y aguacate",
        "mode": "cook",
        "cuisine": "Mexicana",
        "cook_time": 18,
        "price_level": 3,
        "energy": "alta",
        "tags": ["pescado", "fresco", "alto-proteína", "sin-repetir"],
        "description": "Ligero, fresco y con grasas buenas para variar la rutina.",
        "ingredients": [
            ["Filete de salmón", "300 g"],
            ["Tortillas de maíz", "6 unidades"],
            ["Aguacate", "1 unidad"],
            ["Col morada", "1 taza"],
            ["Limón", "2 unidades"],
            ["Yogur griego", "3 cucharadas"],
        ],
        "steps": [
            "Hornea o cocina el salmón a la plancha durante 8 minutos.",
            "Calienta las tortillas y prepara una salsa rápida con yogur y limón.",
            "Sirve con col fileteada y aguacate en láminas.",
        ],
    },
    {
        "name": "Pasta cremosa de champiñones",
        "mode": "cook",
        "cuisine": "Italiana",
        "cook_time": 25,
        "price_level": 2,
        "energy": "baja",
        "tags": ["vegetariano", "comfort", "cremoso", "rápido"],
        "description": "Comfort food sencilla y sin complicaciones para un día pesado.",
        "ingredients": [
            ["Pasta corta", "250 g"],
            ["Champiñones", "250 g"],
            ["Crema de cocina", "200 ml"],
            ["Parmesano", "50 g"],
            ["Ajo", "2 dientes"],
            ["Espinaca", "1 taza"],
        ],
        "steps": [
            "Hierve la pasta hasta que quede al dente.",
            "Saltea ajo y champiñones hasta dorar.",
            "Agrega la crema, el parmesano y la espinaca.",
            "Integra la pasta y ajusta sal y pimienta.",
        ],
    },
    {
        "name": "Ensalada power con garbanzos",
        "mode": "cook",
        "cuisine": "Mediterránea",
        "cook_time": 15,
        "price_level": 1,
        "energy": "alta",
        "tags": ["saludable", "rápido", "vegetariano", "meal-prep"],
        "description": "Muy rápida, fresca y saciante para alguien con poco tiempo.",
        "ingredients": [
            ["Garbanzos cocidos", "1 lata"],
            ["Pepino", "1 unidad"],
            ["Tomates cherry", "1 taza"],
            ["Queso feta", "80 g"],
            ["Aceite de oliva", "2 cucharadas"],
            ["Limón", "1 unidad"],
        ],
        "steps": [
            "Enjuaga los garbanzos y colócalos en un bowl.",
            "Añade pepino, tomate y feta cortados.",
            "Aliña con aceite de oliva, limón y sal.",
        ],
    },
    {
        "name": "Poke bowl delivery",
        "mode": "delivery",
        "cuisine": "Hawaiana",
        "cook_time": 5,
        "price_level": 3,
        "energy": "media",
        "tags": ["delivery", "fresco", "rápido", "saludable"],
        "description": "Ideal para pedir cuando quieres algo ligero y confiable.",
        "ingredients": [],
        "steps": [],
    },
    {
        "name": "Ramen casero express",
        "mode": "cook",
        "cuisine": "Japonesa",
        "cook_time": 22,
        "price_level": 2,
        "energy": "media",
        "tags": ["caliente", "comfort", "weekday", "rápido"],
        "description": "Caliente y reconfortante con pocos pasos y mucho sabor.",
        "ingredients": [
            ["Fideos ramen", "2 paquetes"],
            ["Caldo de pollo", "750 ml"],
            ["Huevos", "2 unidades"],
            ["Espinaca", "1 taza"],
            ["Salsa de soya", "1 cucharada"],
            ["Cebollín", "2 ramas"],
        ],
        "steps": [
            "Calienta el caldo con salsa de soya.",
            "Cuece los huevos 7 minutos y enfríalos.",
            "Añade los fideos al caldo y cocina 3 minutos.",
            "Sirve con espinaca, huevo y cebollín.",
        ],
    },
    {
        "name": "Burrito bowl delivery",
        "mode": "delivery",
        "cuisine": "Tex-Mex",
        "cook_time": 5,
        "price_level": 2,
        "energy": "alta",
        "tags": ["delivery", "protein", "completo", "rápido"],
        "description": "Una opción contundente y práctica para días de mucha carga.",
        "ingredients": [],
        "steps": [],
    },
]

DEFAULT_PROFILE = {
    "name": "Alex",
    "goal": "variedad",
    "preferred_modes": ["cook", "delivery"],
    "favorite_cuisines": ["Asiática", "Mediterránea", "Mexicana"],
    "favorite_ingredients": ["pollo", "aguacate", "arroz"],
    "allergies": ["cacahuate"],
    "disliked_ingredients": ["apio"],
    "weeknight_minutes": 25,
    "budget_level": 2,
}

RECENT_HISTORY = [
    {"dish": "Pasta cremosa de champiñones", "mood": "cansado", "action": "liked", "days_ago": 4},
    {"dish": "Bowl de pollo teriyaki", "mood": "ocupado", "action": "cooked", "days_ago": 2},
    {"dish": "Poke bowl delivery", "mood": "sin tiempo", "action": "ordered", "days_ago": 1},
]


@dataclass
class RecommendationContext:
    mode: str
    mood: str
    time_available: int
    supermarket: str
    wants_variety: bool


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            goal TEXT NOT NULL,
            preferred_modes TEXT NOT NULL,
            favorite_cuisines TEXT NOT NULL,
            favorite_ingredients TEXT NOT NULL,
            allergies TEXT NOT NULL,
            disliked_ingredients TEXT NOT NULL,
            weeknight_minutes INTEGER NOT NULL,
            budget_level INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS dishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            mode TEXT NOT NULL,
            cuisine TEXT NOT NULL,
            cook_time INTEGER NOT NULL,
            price_level INTEGER NOT NULL,
            energy TEXT NOT NULL,
            tags TEXT NOT NULL,
            description TEXT NOT NULL,
            ingredients TEXT NOT NULL,
            steps TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            dish_name TEXT NOT NULL,
            action TEXT NOT NULL,
            mood TEXT,
            created_at TEXT NOT NULL
        );
        """
    )

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        now = datetime.now(timezone.utc).isoformat()
        cur.execute(
            """
            INSERT INTO users (
                id, name, goal, preferred_modes, favorite_cuisines, favorite_ingredients,
                allergies, disliked_ingredients, weeknight_minutes, budget_level, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                USER_ID,
                DEFAULT_PROFILE["name"],
                DEFAULT_PROFILE["goal"],
                json.dumps(DEFAULT_PROFILE["preferred_modes"]),
                json.dumps(DEFAULT_PROFILE["favorite_cuisines"]),
                json.dumps(DEFAULT_PROFILE["favorite_ingredients"]),
                json.dumps(DEFAULT_PROFILE["allergies"]),
                json.dumps(DEFAULT_PROFILE["disliked_ingredients"]),
                DEFAULT_PROFILE["weeknight_minutes"],
                DEFAULT_PROFILE["budget_level"],
                now,
                now,
            ),
        )

    cur.execute("SELECT COUNT(*) FROM dishes")
    if cur.fetchone()[0] == 0:
        for dish in SEED_DISHES:
            cur.execute(
                """
                INSERT INTO dishes (
                    name, mode, cuisine, cook_time, price_level, energy, tags, description, ingredients, steps
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dish["name"],
                    dish["mode"],
                    dish["cuisine"],
                    dish["cook_time"],
                    dish["price_level"],
                    dish["energy"],
                    json.dumps(dish["tags"]),
                    dish["description"],
                    json.dumps(dish["ingredients"]),
                    json.dumps(dish["steps"]),
                ),
            )

    cur.execute("SELECT COUNT(*) FROM interactions")
    if cur.fetchone()[0] == 0:
        now = datetime.now(timezone.utc)
        for item in RECENT_HISTORY:
            created_at = now.timestamp() - item["days_ago"] * 86400
            cur.execute(
                """
                INSERT INTO interactions (user_id, dish_name, action, mood, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    USER_ID,
                    item["dish"],
                    item["action"],
                    item["mood"],
                    datetime.fromtimestamp(created_at, tz=timezone.utc).isoformat(),
                ),
            )

    conn.commit()
    conn.close()


def row_to_profile(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "name": row["name"],
        "goal": row["goal"],
        "preferred_modes": json.loads(row["preferred_modes"]),
        "favorite_cuisines": json.loads(row["favorite_cuisines"]),
        "favorite_ingredients": json.loads(row["favorite_ingredients"]),
        "allergies": json.loads(row["allergies"]),
        "disliked_ingredients": json.loads(row["disliked_ingredients"]),
        "weeknight_minutes": row["weeknight_minutes"],
        "budget_level": row["budget_level"],
    }


def get_profile(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (USER_ID,)).fetchone()
    if row is None:
        raise RuntimeError("No user profile found")
    return row_to_profile(row)


def save_profile(payload: dict[str, Any]) -> dict[str, Any]:
    profile = {
        "name": payload.get("name", DEFAULT_PROFILE["name"]).strip() or DEFAULT_PROFILE["name"],
        "goal": payload.get("goal", DEFAULT_PROFILE["goal"]),
        "preferred_modes": payload.get("preferred_modes", DEFAULT_PROFILE["preferred_modes"]),
        "favorite_cuisines": payload.get("favorite_cuisines", DEFAULT_PROFILE["favorite_cuisines"]),
        "favorite_ingredients": payload.get("favorite_ingredients", DEFAULT_PROFILE["favorite_ingredients"]),
        "allergies": payload.get("allergies", DEFAULT_PROFILE["allergies"]),
        "disliked_ingredients": payload.get("disliked_ingredients", DEFAULT_PROFILE["disliked_ingredients"]),
        "weeknight_minutes": int(payload.get("weeknight_minutes", DEFAULT_PROFILE["weeknight_minutes"])),
        "budget_level": int(payload.get("budget_level", DEFAULT_PROFILE["budget_level"])),
    }

    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        UPDATE users
        SET name = ?, goal = ?, preferred_modes = ?, favorite_cuisines = ?, favorite_ingredients = ?,
            allergies = ?, disliked_ingredients = ?, weeknight_minutes = ?, budget_level = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            profile["name"],
            profile["goal"],
            json.dumps(profile["preferred_modes"]),
            json.dumps(profile["favorite_cuisines"]),
            json.dumps(profile["favorite_ingredients"]),
            json.dumps(profile["allergies"]),
            json.dumps(profile["disliked_ingredients"]),
            profile["weeknight_minutes"],
            profile["budget_level"],
            now,
            USER_ID,
        ),
    )
    conn.commit()
    conn.close()
    return profile


def list_dishes(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM dishes ORDER BY name ASC").fetchall()
    dishes: list[dict[str, Any]] = []
    for row in rows:
        dishes.append(
            {
                "name": row["name"],
                "mode": row["mode"],
                "cuisine": row["cuisine"],
                "cook_time": row["cook_time"],
                "price_level": row["price_level"],
                "energy": row["energy"],
                "tags": json.loads(row["tags"]),
                "description": row["description"],
                "ingredients": json.loads(row["ingredients"]),
                "steps": json.loads(row["steps"]),
            }
        )
    return dishes


def list_history(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT dish_name, action, mood, created_at FROM interactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 12",
        (USER_ID,),
    ).fetchall()
    return [dict(row) for row in rows]


def text_matches_any(text: str, values: list[str]) -> bool:
    lowered = text.lower()
    return any(value.lower() in lowered for value in values if value)


def compute_recommendations(profile: dict[str, Any], dishes: list[dict[str, Any]], history: list[dict[str, Any]], context: RecommendationContext) -> list[dict[str, Any]]:
    recent_names = [item["dish_name"] for item in history[:5]]
    recommendations: list[dict[str, Any]] = []

    for dish in dishes:
        score = 40
        reasons: list[str] = []
        penalties: list[str] = []

        if context.mode != "both":
            if dish["mode"] == context.mode:
                score += 18
                reasons.append(f"encaja con tu modo preferido de hoy: {context.mode}")
            else:
                score -= 14
                penalties.append("no coincide con si quieres cocinar o pedir")
        elif dish["mode"] in profile["preferred_modes"]:
            score += 10
            reasons.append("encaja con tu comportamiento habitual")

        if dish["cuisine"] in profile["favorite_cuisines"]:
            score += 15
            reasons.append(f"tiene cocina {dish['cuisine']} que suele gustarte")

        joined_text = " ".join(
            [dish["name"], dish["description"], " ".join(dish["tags"]), json.dumps(dish["ingredients"], ensure_ascii=False)]
        )

        if text_matches_any(joined_text, profile["favorite_ingredients"]):
            score += 12
            reasons.append("usa ingredientes alineados con tus favoritos")

        if text_matches_any(joined_text, profile["allergies"] + profile["disliked_ingredients"]):
            score -= 100
            penalties.append("contiene algo que no te conviene")

        target_minutes = min(profile["weeknight_minutes"], context.time_available)
        if dish["cook_time"] <= target_minutes:
            score += 14
            reasons.append("entra bien en tu tiempo disponible")
        else:
            overage = dish["cook_time"] - target_minutes
            score -= min(18, overage)
            penalties.append("puede tomar más tiempo del que tienes hoy")

        if dish["price_level"] <= profile["budget_level"]:
            score += 8
            reasons.append("respeta tu presupuesto habitual")
        else:
            score -= 6
            penalties.append("se sale un poco del presupuesto")

        if context.mood in {"cansado", "ocupado", "sin tiempo"} and "rápido" in dish["tags"]:
            score += 9
            reasons.append("es conveniente para un día pesado")

        if profile["goal"] == "variedad" and context.wants_variety and dish["name"] not in recent_names:
            score += 10
            reasons.append("te ayuda a no repetir lo de los últimos días")
        elif dish["name"] in recent_names:
            score -= 18
            penalties.append("la has visto o elegido muy recientemente")

        delivery_bias = 6 if dish["mode"] == "delivery" and context.mood in {"ocupado", "sin tiempo"} else 0
        cook_bias = 6 if dish["mode"] == "cook" and context.mood in {"quiero cocinar", "motivado"} else 0
        score += delivery_bias + cook_bias
        if delivery_bias:
            reasons.append("te quita fricción cuando no tienes energía")
        if cook_bias:
            reasons.append("aprovecha que hoy sí te apetece cocinar")

        recommendations.append(
            {
                **dish,
                "score": score,
                "reasons": reasons[:3],
                "penalties": penalties[:2],
                "supermarket": context.supermarket,
            }
        )

    recommendations.sort(key=lambda item: item["score"], reverse=True)
    return recommendations[:3]


def build_shopping_list(dish: dict[str, Any], supermarket: str) -> list[dict[str, str]]:
    shopping_list: list[dict[str, str]] = []
    for ingredient, quantity in dish.get("ingredients", []):
        shopping_list.append(
            {
                "ingredient": ingredient,
                "quantity": quantity,
                "suggested_store": supermarket,
            }
        )
    return shopping_list


def call_openai_recommendation(profile: dict[str, Any], context: RecommendationContext, recommendations: list[dict[str, Any]]) -> dict[str, Any] | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    input_payload = {
        "profile": profile,
        "context": context.__dict__,
        "recommendations": [
            {
                "name": item["name"],
                "mode": item["mode"],
                "score": item["score"],
                "reasons": item["reasons"],
                "ingredients": item["ingredients"],
                "steps": item["steps"],
            }
            for item in recommendations
        ],
    }

    body = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Eres el motor de IA de AppComida. Debes personalizar recomendaciones de comida para una persona ocupada. "
                            "Responde SIEMPRE en JSON válido con las claves: summary, recipe_tip, shopping_tip. "
                            "La respuesta debe ser breve, útil, cálida y no repetitiva."
                        ),
                    }
                ],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": json.dumps(input_payload, ensure_ascii=False)}],
            },
        ],
    }

    request = Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None

    text_chunks: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                text_chunks.append(content.get("text", ""))

    if not text_chunks:
        return None

    try:
        return json.loads("\n".join(text_chunks))
    except json.JSONDecodeError:
        return None


def serialize_bootstrap() -> dict[str, Any]:
    conn = get_connection()
    profile = get_profile(conn)
    dishes = list_dishes(conn)
    history = list_history(conn)
    context = RecommendationContext(
        mode="both",
        mood="ocupado",
        time_available=profile["weeknight_minutes"],
        supermarket="Mercado Local",
        wants_variety=True,
    )
    recommendations = compute_recommendations(profile, dishes, history, context)
    ai_layer = call_openai_recommendation(profile, context, recommendations)
    conn.close()
    return {
        "profile": profile,
        "history": history,
        "recommendations": [
            {
                **item,
                "shopping_list": build_shopping_list(item, context.supermarket),
            }
            for item in recommendations
        ],
        "ai": ai_layer
        or {
            "summary": "Hoy te propongo opciones distintas a lo más reciente, priorizando rapidez y variedad.",
            "recipe_tip": "Elige cocinar si tienes 20 a 25 minutos y quieres controlar mejor ingredientes y presupuesto.",
            "shopping_tip": f"Si eliges una receta, tu lista de compra ya se agrupa pensando en {context.supermarket}.",
        },
    }


def generate_recommendations(payload: dict[str, Any]) -> dict[str, Any]:
    conn = get_connection()
    profile = get_profile(conn)
    dishes = list_dishes(conn)
    history = list_history(conn)
    context = RecommendationContext(
        mode=payload.get("mode", "both"),
        mood=payload.get("mood", "ocupado"),
        time_available=int(payload.get("time_available", profile["weeknight_minutes"])),
        supermarket=payload.get("supermarket", "Mercado Local"),
        wants_variety=bool(payload.get("wants_variety", True)),
    )
    recommendations = compute_recommendations(profile, dishes, history, context)
    ai_layer = call_openai_recommendation(profile, context, recommendations)
    conn.close()
    return {
        "recommendations": [
            {
                **item,
                "shopping_list": build_shopping_list(item, context.supermarket),
            }
            for item in recommendations
        ],
        "ai": ai_layer
        or {
            "summary": f"Preparé recomendaciones para un momento '{context.mood}' con {context.time_available} minutos disponibles.",
            "recipe_tip": "Elige recetas con 4 pasos o menos para minimizar fricción mental.",
            "shopping_tip": f"La lista de compra se orienta a {context.supermarket} para que vayas directo a lo necesario.",
        },
    }


def record_interaction(payload: dict[str, Any]) -> dict[str, Any]:
    dish_name = payload.get("dish_name")
    action = payload.get("action")
    mood = payload.get("mood", "")
    if not dish_name or not action:
        raise ValueError("dish_name and action are required")

    conn = get_connection()
    conn.execute(
        "INSERT INTO interactions (user_id, dish_name, action, mood, created_at) VALUES (?, ?, ?, ?, ?)",
        (USER_ID, dish_name, action, mood, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    history = list_history(conn)
    conn.close()
    return {"history": history}


def json_response(handler: BaseHTTPRequestHandler, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class AppComidaHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", "/index.html"}:
            index = (STATIC_DIR / "index.html").read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(index)))
            self.end_headers()
            self.wfile.write(index)
            return

        if self.path.startswith("/static/"):
            file_path = BASE_DIR / self.path.lstrip("/")
            if not file_path.exists():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            mime = "text/plain; charset=utf-8"
            if file_path.suffix == ".css":
                mime = "text/css; charset=utf-8"
            elif file_path.suffix == ".js":
                mime = "application/javascript; charset=utf-8"
            content = file_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        if self.path == "/api/bootstrap":
            json_response(self, serialize_bootstrap())
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length) if content_length else b"{}"
        try:
            payload = json.loads(raw_body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            json_response(self, {"error": "Invalid JSON"}, HTTPStatus.BAD_REQUEST)
            return

        try:
            if self.path == "/api/profile":
                json_response(self, {"profile": save_profile(payload)})
                return
            if self.path == "/api/recommendations":
                json_response(self, generate_recommendations(payload))
                return
            if self.path == "/api/interactions":
                json_response(self, record_interaction(payload))
                return
        except ValueError as exc:
            json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        except Exception as exc:  # noqa: BLE001
            json_response(self, {"error": f"Unexpected server error: {exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[{self.log_date_time_string()}] {self.address_string()} - {fmt % args}")


def run() -> None:
    load_env_file()
    init_db()
    port = int(os.getenv("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), AppComidaHandler)
    print(f"AppComida corriendo en http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()

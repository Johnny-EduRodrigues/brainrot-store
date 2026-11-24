from .database import DATABASE_PATH, get_connection


CATEGORIES = ("Animais", "Comidas", "Criaturas", "Personagens especiais")
RARITIES = (
    ("Comum", "#8b95a5"),
    ("Incomum", "#36a66a"),
    ("Raro", "#3984e8"),
    ("Épico", "#a14be0"),
    ("Lendário", "#e7a52f"),
    ("Mítico", "#e34a78"),
    ("Secreto", "#35215e"),
)

SECRET_RARITY_MIGRATION = {
    "jozezini-cltzini": "Épico",
    "igorzini-chatini": "Raro",
    "johnnyzini-simpatiquini": "Lendário",
    "altinini-chimarrini": "Épico",
    "buccizini-maczini": "Mítico",
    "danizini-arcodicionini": "Lendário",
}

IMAGE_EXTENSIONS = {
    "tralalero-tralala": ".png",
    "bombardiro-crocodilo": ".png",
    "ballerina-cappuccina": ".png",
    "cappuccino-assassino": ".png",
    "bombombini-gusini": ".png",
    "brr-brr-patapim": ".png",
    "chimpanzini-bananini": ".png",
    "trippi-troppi": ".png",
    "tung-tung-tung-sahur": ".png",
    "lirili-larila": ".png",
    "boneca-ambalabu": ".png",
    "frigo-camelo": ".png",
    "la-vaca-saturno-saturnita": ".png",
    "bobrito-bandito": ".png",
    "u-din-din-din-din-dun": ".png",
    "ta-ta-ta-ta-sahur": ".png",
    "buccizini-maczini": ".png",
    "danizini-arcodicionini": ".png",
    "igorzini-chatini": ".png",
    "johnnyzini-simpatiquini": ".png",
    "jozezini-cltzini": ".png",
    "altinini-chimarrini": ".png",
}

BRAINROTS = (
    ("tralalero-tralala", "Tralalero Tralala", "Um tubarão de tênis que transforma qualquer passeio em desfile aquático.", 4990, 15, "Animais", "Raro", "🦈"),
    ("bombardiro-crocodilo", "Bombardiro Crocodilo", "O crocodilo voador que chega fazendo barulho e sai deixando histórias.", 12990, 5, "Animais", "Lendário", "🐊"),
    ("ballerina-cappuccina", "Ballerina Cappuccina", "Uma bailarina elegante que gira tão rápido que até o café fica tonto.", 8990, 10, "Comidas", "Épico", "☕"),
    ("cappuccino-assassino", "Cappuccino Assassino", "Pequeno, espumante e perigosamente bom em desaparecer com biscoitos.", 11990, 7, "Comidas", "Lendário", "🥷"),
    ("bombombini-gusini", "Bombombini Gusini", "Um ganso com atitude explosiva e um talento natural para a confusão.", 5990, 12, "Animais", "Raro", "🪿"),
    ("brr-brr-patapim", "Brr Brr Patapim", "A criatura da floresta que marca o ritmo com passos e sons inconfundíveis.", 2990, 20, "Criaturas", "Incomum", "🌳"),
    ("chimpanzini-bananini", "Chimpanzini Bananini", "Metade macaco, metade lanche: especialista em fugir com a última banana.", 7990, 8, "Animais", "Épico", "🐒"),
    ("trippi-troppi", "Trippi Troppi", "Um viajante lendário que nunca anda em linha reta — e prefere assim.", 14990, 4, "Criaturas", "Lendário", "🌀"),
    ("tung-tung-tung-sahur", "Tung Tung Tung Sahur", "Seu despertador favorito: aparece no horário e nunca aceita soneca.", 19990, 3, "Personagens especiais", "Mítico", "🥁"),
    ("lirili-larila", "Lirili Larila", "Uma presença rara que passeia pelo deserto cantarolando melodias improváveis.", 5490, 12, "Criaturas", "Raro", "🌵"),
    ("boneca-ambalabu", "Boneca Ambalabu", "Uma boneca simpática com passos saltitantes e energia para o dia inteiro.", 3490, 18, "Personagens especiais", "Incomum", "🪆"),
    ("frigo-camelo", "Frigo Camelo", "Carrega refrescos pelo deserto e nunca reclama do calor — nem do peso.", 9490, 8, "Animais", "Épico", "🐪"),
    ("la-vaca-saturno-saturnita", "La Vaca Saturno Saturnita", "Uma vaca cósmica que ordenha estrelas e passeia entre os planetas.", 24990, 2, "Animais", "Mítico", "🐄"),
    ("bobrito-bandito", "Bobrito Bandito", "O bandido mais adorável do bairro: rouba corações, não o estoque.", 1990, 25, "Personagens especiais", "Comum", "🤠"),
    ("u-din-din-din-din-dun", "U Din Din Din Din Dun", "Uma melodia ambulante que transforma qualquer fila em karaokê.", 6490, 10, "Personagens especiais", "Raro", "🎵"),
    ("ta-ta-ta-ta-sahur", "Ta Ta Ta Ta Sahur", "O parceiro rítmico que anuncia a madrugada com muita personalidade.", 8490, 8, "Personagens especiais", "Épico", "🥁"),
    ("jozezini-cltzini", "Jozezini CLTzini (CLT)", "Bate ponto com estilo, entrega tudo antes do prazo e ainda sobra café para a equipe.", 8990, 10, "Personagens especiais", "Secreto", "💼"),
    ("igorzini-chatini", "Igorzini Chatini", "Sempre online, responde com uma figurinha certeira e nunca deixa o grupo no vácuo.", 5990, 12, "Personagens especiais", "Secreto", "💬"),
    ("johnnyzini-simpatiquini", "Johnnyzini Simpatiquini", "Carisma lendário: faz amizade até com quem só entrou para olhar a vitrine.", 12990, 6, "Personagens especiais", "Secreto", "😎"),
    ("altinini-chimarrini", "Altinini Chimarrini", "Gurizinho de respeito: compartilha o mate, conta causos e aquece qualquer roda.", 9490, 8, "Personagens especiais", "Secreto", "🧉"),
    ("buccizini-maczini", "Buccizini Maczini", "Uma lenda intergaláctica com fome de aventura e um talento especial para batatas.", 19990, 3, "Comidas", "Secreto", "🍟"),
    ("danizini-arcodicionini", "Danizini Arcodicionini", "Especialista em clima perfeito: resolve o calor e melhora o astral num clique.", 11990, 7, "Personagens especiais", "Secreto", "❄️"),
)


def popular_banco(database_path=DATABASE_PATH):
    """Insere o catálogo inicial sem alterar dados já cadastrados ou editados."""
    with get_connection(database_path) as connection:
        connection.executemany(
            "INSERT OR IGNORE INTO categories (name) VALUES (?)",
            ((name,) for name in CATEGORIES),
        )
        connection.executemany(
            "INSERT OR IGNORE INTO rarities (name, color) VALUES (?, ?)",
            RARITIES,
        )

        category_ids = {
            row["name"]: row["id"]
            for row in connection.execute("SELECT id, name FROM categories")
        }
        rarity_ids = {
            row["name"]: row["id"]
            for row in connection.execute("SELECT id, name FROM rarities")
        }
        connection.executemany(
            """
            INSERT OR IGNORE INTO brainrots
                (slug, name, description, price_cents, stock, image_path, category_id, rarity_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (
                    slug,
                    name,
                    description,
                    price,
                    stock,
                    f"/public/brainrots/{slug}{IMAGE_EXTENSIONS.get(slug, '.svg')}",
                    category_ids[category],
                    rarity_ids[rarity],
                )
                for slug, name, description, price, stock, category, rarity, _emoji in BRAINROTS
            ),
        )
        for slug, extension in IMAGE_EXTENSIONS.items():
            connection.execute(
                """
                UPDATE brainrots
                SET image_path = ?
                WHERE slug = ? AND image_path = ?
                """,
                (
                    f"/public/brainrots/{slug}{extension}",
                    slug,
                    f"/public/brainrots/{slug}.svg",
                ),
            )
        migration_key = "additional-brainrots-secret-rarity-v1"
        migration = connection.execute(
            "SELECT 1 FROM seed_migrations WHERE migration_key = ?",
            (migration_key,),
        ).fetchone()
        if migration is None:
            secret_id = rarity_ids["Secreto"]
            for slug, previous_rarity in SECRET_RARITY_MIGRATION.items():
                connection.execute(
                    """
                    UPDATE brainrots
                    SET rarity_id = ?
                    WHERE slug = ? AND rarity_id = ?
                    """,
                    (secret_id, slug, rarity_ids[previous_rarity]),
                )
            connection.execute(
                "INSERT INTO seed_migrations (migration_key) VALUES (?)",
                (migration_key,),
            )

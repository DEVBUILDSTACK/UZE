"""Seed the sports taxonomy (Sport / SportVariant / EventCategory / PathwayLevel).

Idempotent: every INSERT is ON CONFLICT DO NOTHING against the unique keys.
Run anywhere with DIRECT_URL set (Neon direct connection).
Sourced 2026-10-17: ISA LA28 surfing qualification; World Lacrosse sixes;
USA Lacrosse youth age bands.
"""
import os
import urllib.parse

import psycopg2

SPORTS = ["Surfing", "Lacrosse"]

VARIANTS = [
    # (sport, name, playersPerSide, olympic, fieldSpec, notes)
    ("Surfing", "Shortboard", None, True, "Lower Trestles, San Clemente (LA28)",
     "Olympic discipline. LA28: 48 athletes (24M/24W), Jul 15-18 2028. "
     "Qualification Sep 2026-Jun 2028 via WSL Championship Tour (top 8/gender), "
     "ISA World Surfing Games (2026/2027 team slots + 2028 top 7/gender), continental games."),
    ("Lacrosse", "Sixes", 6, True, "70m x 36m outdoor",
     "World Lacrosse Olympic format (rules approved Nov 2020). 6v6 (5 field + goalie); "
     "4x8-min quarters running time; 30-sec shot clock; 12-player rosters; faceoffs only "
     "at quarter starts; no specialist positions, no long crosses, no offsides. "
     "Olympic debut LA28 (first medal lacrosse since 1908); 6-team tournaments/gender. "
     "2027 Sixes Worlds (Colorado Springs) is the primary qualifier."),
    ("Lacrosse", "Men's Field", 10, False, "110 x 60 yd",
     "Traditional 10v10 (3 attack, 3 midfield, 3 defense, 1 goalie); ~60-min games; contact allowed."),
    ("Lacrosse", "Women's Field", 12, False, "~120 x 65 yd",
     "Traditional 12v12 (1 goalie, 3 attackers, 5 midfielders, 3 defenders); halves format "
     "(~50 min); limited/no contact; 8-meter arc + 12-meter fan."),
    ("Lacrosse", "Box", 6, False, "indoor",
     "6v6 (5 runners + goalie) indoor; 4x15-min quarters; shot clock; smaller goals."),
]

CATEGORIES = [
    # (name, tier)
    ("Olympic Games", 100),
    ("World Championship", 80),
    ("Qualifier", 70),
    ("Continental Games", 60),
    ("Pro Tour", 50),
    ("Youth Club", 20),
]

LEVELS = [
    # (sport, code, name, order, ageBand, cutoffRule) — sport None = cross-sport
    ("Lacrosse", "8U", "8U (grades 1-2)", 10, "8U",
     "Aug 31 preceding (USA Lacrosse; some leagues use Dec 31 / Apr 15)"),
    ("Lacrosse", "10U", "10U (grades 3-4)", 20, "10U",
     "Aug 31 preceding (USA Lacrosse; some leagues use Dec 31 / Apr 15)"),
    ("Lacrosse", "12U", "12U (grades 5-6)", 30, "12U",
     "Aug 31 preceding (USA Lacrosse; some leagues use Dec 31 / Apr 15)"),
    ("Lacrosse", "14U", "14U (grades 7-8)", 40, "14U",
     "Aug 31 preceding; players on any HS-level team in the same season are ineligible"),
    ("Lacrosse", "HS_FRESHMAN", "High School Freshman", 50, None, None),
    ("Lacrosse", "HS_JV", "High School Junior Varsity", 60, None, None),
    ("Lacrosse", "HS_VARSITY", "High School Varsity", 70, None, None),
    ("Lacrosse", "CLUB", "Club (year-round travel/select)", 75, None,
     "Tryout-based independent orgs; highest-skill youth competition; parallel to school ball"),
    ("Lacrosse", "NCAA", "NCAA College", 80, None, None),
    ("Lacrosse", "WORLDS", "World Lacrosse Championships", 90, None, None),
    (None, "OLYMPIC", "Olympic Games", 100, None, None),
]


def main() -> None:
    url = os.environ.get("DIRECT_URL") or os.environ["DATABASE_URL"]
    p = urllib.parse.urlparse(url)
    conn = psycopg2.connect(
        host=p.hostname, port=p.port or 5432, user=p.username,
        password=p.password, dbname=p.path.lstrip("/"), sslmode="require",
    )
    conn.autocommit = True
    cur = conn.cursor()

    sport_ids = {}
    for name in SPORTS:
        cur.execute(
            'INSERT INTO "Sport" (name) VALUES (%s) '
            'ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name '
            'RETURNING id',
            (name,),
        )
        row = cur.fetchone()
        if row is None:
            cur.execute('SELECT id FROM "Sport" WHERE name=%s', (name,))
            row = cur.fetchone()
        sport_ids[name] = row[0]

    for sport, name, pps, olympic, field, notes in VARIANTS:
        cur.execute(
            'INSERT INTO "SportVariant" '
            '("sportId", name, "playersPerSide", olympic, "fieldSpec", notes) '
            'VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT ("sportId", name) DO NOTHING',
            (sport_ids[sport], name, pps, olympic, field, notes),
        )

    for name, tier in CATEGORIES:
        cur.execute(
            'INSERT INTO "EventCategory" (name, tier) VALUES (%s,%s) '
            'ON CONFLICT (name) DO NOTHING',
            (name, tier),
        )

    for sport, code, name, order, band, cutoff in LEVELS:
        sid = sport_ids[sport] if sport else None
        if sid is None:
            # NULL sportId never conflicts on the unique key; guard manually.
            cur.execute(
                'SELECT 1 FROM "PathwayLevel" WHERE "sportId" IS NULL AND code=%s',
                (code,),
            )
            if cur.fetchone():
                continue
        cur.execute(
            'INSERT INTO "PathwayLevel" '
            '("sportId", code, name, "order", "ageBand", "cutoffRule") '
            'VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT ("sportId", code) DO NOTHING',
            (sid, code, name, order, band, cutoff),
        )

    conn.commit()
    cur.execute('SELECT COUNT(*) FROM "Sport"')
    print("sports:", cur.fetchone()[0])
    cur.execute('SELECT COUNT(*) FROM "SportVariant"')
    print("variants:", cur.fetchone()[0])
    cur.execute('SELECT COUNT(*) FROM "EventCategory"')
    print("categories:", cur.fetchone()[0])
    cur.execute('SELECT COUNT(*) FROM "PathwayLevel"')
    print("levels:", cur.fetchone()[0])
    conn.close()


if __name__ == "__main__":
    main()

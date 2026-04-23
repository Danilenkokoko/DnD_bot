CLASS_DATA = {
    "Воин": {
        "hit_die": 10,
        "skills": ["Athletics", "Intimidation"],
        "equipment": ["Sword", "Shield", "Armor"],
        "spells": []
    },
    "Маг": {
        "hit_die": 6,
        "skills": ["Arcana", "History"],
        "equipment": ["Staff", "Spellbook"],
        "spells": ["Fire Bolt", "Mage Armor"]
    },
    "Плут": {
        "hit_die": 8,
        "skills": ["Stealth", "Acrobatics"],
        "equipment": ["Dagger", "Light Armor"],
        "spells": []
    }
}

def modifier(stat):
    return (stat - 10) // 2


def calc_hp(char_class, con):
    return CLASS_DATA[char_class]["hit_die"] + modifier(con)


def calc_ac(dex):
    return 10 + modifier(dex)
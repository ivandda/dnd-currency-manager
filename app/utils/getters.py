from app.models import models
from app.schemas.party import PartyResponse


# CHARACTERS---------------------------------------------------:
def get_all_characters(db):
    return db.query(models.Characters).all()


def get_all_character_names(db):
    return [character.name for character in get_all_characters(db)]


def get_all_character_ids(db):
    return [character.id for character in get_all_characters(db)]


def get_character_by_id(db, character_id):
    return db.query(models.Characters).filter(models.Characters.id == character_id).first()


def get_character_name(db, character_id):
    return get_character_by_id(db, character_id).name


def get_all_parties_character_is_in(db, character_id):
    return db.query(models.Parties).filter(models.Parties.characters.any(id=character_id)).all()


#
#
#
#
# WALLET---------------------------------------------------:

def get_all_wallets(db):
    return db.query(models.Wallet).all()


def get_all_wallet_ids(db):
    return [wallet.id for wallet in get_all_wallets(db)]


def get_wallet_by_id(db, wallet_id):
    return db.query(models.Wallet).filter(models.Wallet.id == wallet_id).first()


def get_wallet_with_character_id(db, character_id):
    return db.query(models.Wallet).filter(models.Wallet.character_owner_id == character_id).first()


def get_money_in_wallet(db, wallet_id):
    wallet = get_wallet_by_id(db, wallet_id)
    return wallet.money


def get_money_in_character_wallet(db, character_id: int) -> int:
    character_wallet = get_wallet_with_character_id(db, character_id)
    character_money = get_money_in_wallet(db, character_wallet.id)

    return character_money


# def get_all_info_in_wallet(db, wallet_id):


#
#
#
#
# PARTY---------------------------------------------------:
def get_all_parties(db):
    return db.query(models.Parties).all()


def get_all_party_names(db):
    return [party.name for party in get_all_parties(db)]


def get_all_party_ids(db):
    return [party.id for party in get_all_parties(db)]


def get_party_by_id(db, party_id):
    return db.query(models.Parties).filter(models.Parties.id == party_id).first()


def get_all_characters_in_party(db, party_id):
    party = get_party_by_id(db, party_id)
    return party.characters


def get_all_characters_id_in_party(db, party_id):
    party = get_party_by_id(db, party_id)
    return [character.id for character in party.characters]


def get_all_info_of_party(db, party_id) -> PartyResponse:
    party = get_party_by_id(db, party_id)
    return PartyResponse(id=party.id, name=party.name, created_at=party.created_at)

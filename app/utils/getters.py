from uuid import UUID

from app.models import models, auth
from app.schemas.characters import CharacterAllInfoResponse
from app.schemas.parties import PartyAllInfoResponse, PartyResponse
from app.utils.currency_convertions import convert_to_simplified


# CHARACTERS---------------------------------------------------:
def get_all_characters(db):
    return db.query(models.Characters).all()


def get_all_characters_with_user_id(db, user_id):
    # return db.query(models.Characters).filter(models.Characters.user_id == user_id).all()
    return (db.query(models.Characters).join(models.users_characters)
            .filter(models.users_characters.c.user_id == user_id).all())


def get_character_with_user_id_and_character_id(db, user_id, character_id):
    return (db.query(models.Characters).join(models.users_characters)
            .filter(models.users_characters.c.user_id == user_id)
            .filter(models.Characters.id == character_id).first())


def get_all_character_names(db):
    return [character.name for character in get_all_characters(db)]


def get_all_character_ids(db):
    return [character.id for character in get_all_characters(db)]


def get_character_by_id(db, character_id):
    return db.query(models.Characters).filter(models.Characters.id == character_id).first()


def get_user_id_by_character_id(db, character_id):
    return get_character_by_id(db, character_id).user_id


def get_character_name(db, character_id):
    return get_character_by_id(db, character_id).name


def get_all_parties_character_is_in(db, character_id):
    return db.query(models.Parties).filter(models.Parties.characters.any(id=character_id)).all()


def get_all_character_info(db, character_id) -> CharacterAllInfoResponse:
    character = get_character_by_id(db, character_id)
    character_money_simplified = convert_to_simplified(get_money_in_character_wallet(db, character_id))
    all_character_parties = [get_info_of_party_for_character(db, party.id)
                             for party in get_all_parties_character_is_in(db, character_id)]
    return CharacterAllInfoResponse(id=character.id
                                    , name=character.name
                                    , wallet=character_money_simplified
                                    , parties=all_character_parties
                                    , created_at=character.created_at)


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
    return db.query(models.Wallet).filter(models.Wallet.character_id == character_id).first()


def get_money_in_wallet(db, wallet_id):
    wallet = get_wallet_by_id(db, wallet_id)
    return wallet.money_copper


def get_money_in_character_wallet(db, character_id: UUID) -> int:
    character_wallet = get_wallet_with_character_id(db, character_id)
    character_money = get_money_in_wallet(db, character_wallet.id)

    return character_money


def get_character_wallet_with_user_id_and_character_id(db, user_id: UUID, character_id: UUID):
    character_wallet = db.query(models.Wallet).join(models.Characters).join(models.users_characters).filter(models.users_characters.c.user_id == user_id).filter(models.Characters.id == character_id).first()
    return character_wallet



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


def get_info_of_party_for_character(db, party_id) -> PartyResponse:
    party = get_party_by_id(db, party_id)
    return PartyResponse(id=party.id,
                         name=party.name,
                         created_at=party.created_at)


def get_all_info_of_party(db, party_id) -> PartyAllInfoResponse:
    party = get_party_by_id(db, party_id)
    all_characters_in_party = [get_all_character_info(db, character.id)
                               for character in get_all_characters_in_party(db, party_id)]
    dms_ids = [dm.id for dm in get_dms_of_party(db, party_id)]
    return PartyAllInfoResponse(id=party.id,
                                name=party.name,
                                characters=all_characters_in_party,
                                created_at=party.created_at,
                                dms=dms_ids)


def get_dms_of_party(db, party_id):
    return db.query(auth.User).join(auth.dm_parties).filter(auth.dm_parties.c.party_id == party_id).all()


# Users---------------------------------------------------:

def get_user_by_id(db, user_id):
    return db.query(auth.User).filter(auth.User.id == user_id).first()

from datetime import datetime

from domain.entities.telescope import Telescope


def convert_telescope_to_mongo_doc(telescope: Telescope) -> dict:
    return {
        'oid': telescope.oid,
        'name': telescope.name,
        'connection_state': telescope.connection_state,
        'tracking_enabled': telescope.tracking_enabled,
        'created_at': telescope.created_at,
    }


def convert_mongo_doc_to_telescope(doc: dict) -> Telescope:
    created_at = doc.get('created_at')
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)

    return Telescope(
        oid=doc['oid'],
        name=doc.get('name', 'Primary Telescope'),
        connection_state=doc.get('connection_state', 'disconnected'),
        tracking_enabled=doc.get('tracking_enabled', False),
        created_at=created_at or datetime.now(),
    )

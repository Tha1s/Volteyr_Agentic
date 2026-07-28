import csv
import io

import duckdb
import pytest
from unittest.mock import patch

import src.db.connection as conn_mod
from src.db.connection import close
from src.db.loader import load_csv_from_dictreader


@pytest.fixture
def db_conn():
    conn = duckdb.connect(":memory:")
    conn_mod._local.connection = conn
    conn.execute("""
        CREATE TABLE products (
            product_id BIGINT PRIMARY KEY,
            product_type VARCHAR,
            category VARCHAR,
            product_tags VARCHAR,
            images_array VARCHAR,
            vendor VARCHAR,
            inventory_quantity BIGINT,
            gross_amount_exc_tax_product DOUBLE,
            description VARCHAR
        )
    """)
    conn.execute("CREATE SEQUENCE enrichissements_seq START 1")
    conn.execute("""
        CREATE TABLE enrichissements (
            id BIGINT PRIMARY KEY DEFAULT nextval('enrichissements_seq'),
            product_id BIGINT,
            enriched_description VARCHAR,
            material VARCHAR,
            care_instructions VARCHAR,
            style VARCHAR,
            seo_keywords VARCHAR,
            model_used VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    yield conn
    close()


@pytest.fixture
def mock_categories():
    with patch("src.db.loader.auto_fill_categories"), \
         patch("src.db.loader.load_category_map") as mock_map:
        mock_map.return_value = {}
        yield


def _make_csv_reader(lines: str) -> csv.DictReader:
    return csv.DictReader(io.StringIO(lines.strip()))


CSV_ALL_COLUMNS = """product_id,product_type,product_tags,images_array,vendor,inventory_quantity,gross_amount_exc_tax_product,description
1,Robe,été,image1.jpg,Sandro,10,150.0,Belle robe en soie
2,Pantalon,hiver,image2.jpg,Maje,5,120.0,Pantalon élégant
3,T-Shirt,,image3.jpg,AMI,20,60.0,T-shirt coton bio"""


def test_load_valid_csv(db_conn, mock_categories):
    reader = _make_csv_reader(CSV_ALL_COLUMNS)
    count = load_csv_from_dictreader(reader)
    assert count == 3
    row_count = db_conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    assert row_count == 3


def test_load_valid_csv_correct_data(db_conn, mock_categories):
    reader = _make_csv_reader(CSV_ALL_COLUMNS)
    load_csv_from_dictreader(reader)
    row = db_conn.execute(
        "SELECT product_id, vendor, inventory_quantity, gross_amount_exc_tax_product "
        "FROM products WHERE product_id = 1"
    ).fetchone()
    assert row[0] == 1
    assert row[1] == "Sandro"
    assert row[2] == 10
    assert row[3] == 150.0


def test_load_missing_columns(db_conn, mock_categories):
    csv_data = "product_id,product_type\n1,Robe"
    reader = _make_csv_reader(csv_data)
    with pytest.raises(ValueError, match="Colonnes manquantes"):
        load_csv_from_dictreader(reader)


def test_load_empty_csv(db_conn, mock_categories):
    csv_data = "product_id,product_type,product_tags,images_array,vendor,inventory_quantity,gross_amount_exc_tax_product,description"
    reader = _make_csv_reader(csv_data)
    with pytest.raises(Exception):
        load_csv_from_dictreader(reader)


def test_load_invalid_numbers_skip(db_conn, mock_categories):
    csv_data = """product_id,product_type,product_tags,images_array,vendor,inventory_quantity,gross_amount_exc_tax_product,description
ABC,Robe,été,image1.jpg,Sandro,10,150.0,Mauvaise ligne
2,Pantalon,hiver,image2.jpg,Maje,5,120.0,OK"""
    reader = _make_csv_reader(csv_data)
    count = load_csv_from_dictreader(reader)
    assert count == 1
    row_count = db_conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    assert row_count == 1
    surviving = db_conn.execute("SELECT product_id FROM products").fetchone()[0]
    assert surviving == 2


def test_load_invalid_inventory_skip(db_conn, mock_categories):
    csv_data = """product_id,product_type,product_tags,images_array,vendor,inventory_quantity,gross_amount_exc_tax_product,description
1,Robe,été,image1.jpg,Sandro,XYZ,150.0,Belle robe
2,Pantalon,hiver,image2.jpg,Maje,5,120.0,OK"""
    reader = _make_csv_reader(csv_data)
    count = load_csv_from_dictreader(reader)
    assert count == 1
    surviving = db_conn.execute("SELECT product_id FROM products").fetchone()[0]
    assert surviving == 2


def test_load_invalid_price_skip(db_conn, mock_categories):
    csv_data = """product_id,product_type,product_tags,images_array,vendor,inventory_quantity,gross_amount_exc_tax_product,description
1,Robe,été,image1.jpg,Sandro,10,N/A,Belle robe
2,Pantalon,hiver,image2.jpg,Maje,5,120.0,OK"""
    reader = _make_csv_reader(csv_data)
    count = load_csv_from_dictreader(reader)
    assert count == 1
    surviving = db_conn.execute("SELECT product_id FROM products").fetchone()[0]
    assert surviving == 2


def test_load_idempotent(db_conn, mock_categories):
    reader1 = _make_csv_reader(CSV_ALL_COLUMNS)
    count1 = load_csv_from_dictreader(reader1)
    assert count1 == 3

    reader2 = _make_csv_reader(CSV_ALL_COLUMNS)
    count2 = load_csv_from_dictreader(reader2)
    assert count2 == 3

    row_count = db_conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    assert row_count == 3

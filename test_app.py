import tempfile
import unittest
from pathlib import Path

import app as app_module


class ClientCrudTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        app_module.DB_PATH = Path(self.tmpdir.name) / "test.db"
        app_module.init_db()

        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def _create_client(self, **overrides):
        data = {
            "name": "Ana García",
            "email": "ana@example.com",
            "phone": "555-0001",
            "company": "ACME",
            "notes": "Cliente nuevo",
        }
        data.update(overrides)
        return self.client.post("/clients/new", data=data, follow_redirects=True)

    def _insert_client(self, name="Ana", email="ana@example.com"):
        with app_module.app.app_context():
            db = app_module.get_db()
            cursor = db.execute(
                "INSERT INTO clients (name, email, phone, company, notes) VALUES (?, ?, ?, ?, ?)",
                (name, email, "555", "Empresa", "Nota"),
            )
            db.commit()
            return cursor.lastrowid

    def test_create_and_list_client(self):
        response = self._create_client()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Cliente creado correctamente.".encode(), response.data)
        self.assertIn("Ana García".encode(), response.data)
        self.assertIn("ana@example.com".encode(), response.data)

    def test_validation_invalid_email(self):
        response = self._create_client(email="correo-invalido")

        self.assertEqual(response.status_code, 200)
        self.assertIn("El correo electrónico no es válido.".encode(), response.data)

    def test_client_detail(self):
        client_id = self._insert_client()

        response = self.client.get(f"/clients/{client_id}")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Detalle de cliente".encode(), response.data)
        self.assertIn("ana@example.com".encode(), response.data)

    def test_edit_client(self):
        client_id = self._insert_client()

        response = self.client.post(
            f"/clients/{client_id}/edit",
            data={
                "name": "Ana Actualizada",
                "email": "ana2@example.com",
                "phone": "555-0002",
                "company": "Nueva Empresa",
                "notes": "Actualizada",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Cliente actualizado correctamente.".encode(), response.data)
        self.assertIn("Ana Actualizada".encode(), response.data)

    def test_delete_client(self):
        client_id = self._insert_client()

        response = self.client.post(f"/clients/{client_id}/delete", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Cliente eliminado correctamente.".encode(), response.data)


if __name__ == "__main__":
    unittest.main()

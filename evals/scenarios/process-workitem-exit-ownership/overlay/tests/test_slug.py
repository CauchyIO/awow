import unittest

from src.slug import slug


class TestSlug(unittest.TestCase):
    def test_warehouse_label_is_normalized(self):
        self.assertEqual(slug("Warehouse Label"), "warehouse-label")


if __name__ == "__main__":
    unittest.main()

import unittest
import json
from app import app, db
from models import Shipment, Quote, QuoteHistory

class TransPakTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after each test method."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_index_page_loads(self):
        """Test that the main page loads correctly."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'TransPak AI Quoter', response.data)
        self.assertIn(b'AI Agent Activity Monitor', response.data)
    
    def test_generate_quote_missing_required_fields(self):
        """Test quote generation with missing required fields."""
        test_data = {
            'item_description': 'Test Item',
            # Missing required fields like dimensions, weight, etc.
        }
        
        response = self.client.post('/generate_quote', data=test_data)
        self.assertEqual(response.status_code, 200)
        # Should return to form with validation errors
    
    def test_quotes_list_page(self):
        """Test that the quotes list page loads."""
        response = self.client.get('/quotes')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Quote History', response.data)
    
    def test_admin_dashboard_page(self):
        """Test that the admin dashboard loads."""
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'System Dashboard', response.data)
        self.assertIn(b'AI Agents Active', response.data)
    
    def test_view_quote_not_found(self):
        """Test viewing a non-existent quote."""
        response = self.client.get('/quote/999')
        self.assertEqual(response.status_code, 404)
    
    def test_download_quote_not_found(self):
        """Test downloading a non-existent quote."""
        response = self.client.get('/download_quote/999')
        self.assertEqual(response.status_code, 404)
    
    def test_database_models(self):
        """Test database model creation and relationships."""
        with self.app.app_context():
            # Test Shipment creation
            shipment = Shipment(
                item_description="Test Item",
                dimensions="10x10x10",
                weight="100 lbs",
                origin="Test Origin",
                destination="Test Destination"
            )
            db.session.add(shipment)
            db.session.commit()
            
            # Test Quote creation
            quote = Quote(
                shipment_id=shipment.id,
                quote_content="Test quote content",
                status="generated"
            )
            db.session.add(quote)
            db.session.commit()
            
            # Test relationships
            self.assertEqual(len(shipment.quotes), 1)
            self.assertEqual(quote.shipment.item_description, "Test Item")
    
    def test_light_theme_css(self):
        """Test that the light theme styling is applied."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # Check for light theme CSS variables
        self.assertIn(b'--neutral-50: #fafafa', response.data)
        self.assertIn(b'Inter', response.data)  # Inter font
        self.assertIn(b'--primary-color: #6366f1', response.data)

if __name__ == '__main__':
    unittest.main()
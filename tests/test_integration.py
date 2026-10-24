"""Dependency-backed tests using real synthetic PDFs and Streamlit AppTest."""
import importlib.util
import json
import unittest
from unittest.mock import patch
import review

@unittest.skipUnless(importlib.util.find_spec('pymupdf'), 'PyMuPDF not installed')
class RealPDFTests(unittest.TestCase):
    def pdf(self, text=None, encrypted=False):
        import pymupdf
        with pymupdf.open() as doc:
            page = doc.new_page()
            if text:
                page.insert_text((72, 72), text)
            if encrypted:
                return doc.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw='owner', user_pw='secret')
            return doc.tobytes()

    def test_real_text_pdf(self):
        text = 'Synthetic candidate. Built a Python dashboard for a student society.'
        self.assertIn(text, review.extract_pdf(self.pdf(text)))

    def test_real_blank_scanned_equivalent(self):
        with self.assertRaisesRegex(review.ReviewError, 'readable'):
            review.extract_pdf(self.pdf())

    def test_real_encrypted(self):
        with self.assertRaisesRegex(review.ReviewError, 'encrypted'):
            review.extract_pdf(self.pdf('Synthetic CV', True))

    def test_real_corrupt(self):
        with self.assertRaisesRegex(review.ReviewError, 'Unable'):
            review.extract_pdf(b'%PDF-broken')

@unittest.skipUnless(importlib.util.find_spec('streamlit'), 'Streamlit not installed')
class AppTests(unittest.TestCase):
    def test_demo_no_api_and_rerun_persistence(self):
        from streamlit.testing.v1 import AppTest
        with patch('review.analyse', side_effect=AssertionError('No API allowed')):
            app = AppTest.from_file('app.py').run()
            self.assertEqual(len(app.exception), 0)
            app.radio[0].set_value('Synthetic demo — no API calls').run()
            next(b for b in app.button if b.label == 'Show synthetic feedback').click().run()
            self.assertIn('SYNTHETIC DEMO', app.session_state['demo_report'])
            app.run()
            self.assertIn('SYNTHETIC DEMO', app.session_state['demo_report'])
            next(b for b in app.button if b.label == 'Clear session data').click().run()
            self.assertNotIn('demo_report', app.session_state)
            self.assertEqual(len(app.exception), 0)

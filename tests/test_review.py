"""Offline tests: synthetic CVs, generated PDF parser doubles, mocked SDK only."""
import copy
import json
import sys
import types
import unittest
from unittest.mock import Mock, MagicMock, patch
import review

class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.cv, self.result = review.demo()

    def test_demo_and_export(self):
        output = review.report(self.result, "Analyst", "Entry", True)
        for text in ("SYNTHETIC DEMO", "Strengths", "Improvements", "Evidence Gaps", "Questions"):
            self.assertIn(text, output)

    def test_fabricated_quote_rejected(self):
        self.result['strengths'][0]['quote'] = 'Increased revenue by 90%'
        with self.assertRaisesRegex(review.ReviewError, 'quotation'):
            review.validate_feedback(json.dumps(self.result), self.cv)

    def test_job_description_cannot_supply_quote(self):
        self.result['improvements'][0]['quote'] = 'Kubernetes expert'
        with self.assertRaises(review.ReviewError):
            review.validate_feedback(json.dumps(self.result), self.cv)

    def test_whitespace_normalisation(self):
        review.validate_feedback(json.dumps(self.result), self.cv.replace('Python dashboard', 'Python\n dashboard'))

    def test_invalid_schema(self):
        for raw in ('null', '[]', '{}', 'not json', json.dumps(dict(self.result, questions=[]))):
            with self.subTest(raw=raw), self.assertRaises(review.ReviewError):
                review.validate_feedback(raw, self.cv)

    def test_strength_requires_quote(self):
        self.result['strengths'][0]['quote'] = ''
        with self.assertRaises(review.ReviewError):
            review.validate_feedback(json.dumps(self.result), self.cv)

    def test_priority_sort(self):
        item = copy.deepcopy(self.result['improvements'][0])
        item['priority'] = 'Low'
        self.result['improvements'].insert(0, item)
        validated = review.validate_feedback(json.dumps(self.result), self.cv)
        self.assertEqual(validated['improvements'][0]['priority'], 'High')

    def test_inputs_stop_before_client(self):
        factory = MagicMock()
        for cv, role, jd, key in [(self.cv, 'Analyst', '', ''), ('short', 'Analyst', '', 'fake'), ('a'*24001, 'Analyst', '', 'fake'), (self.cv, '', '', 'fake'), (self.cv, 'Analyst', 'a'*12001, 'fake')]:
            with self.assertRaises(review.ReviewError):
                review.analyse(cv, role, 'Entry', jd, key, client_factory=factory)
        factory.assert_not_called()

    def sdk(self):
        return types.SimpleNamespace(**{name: type(name, (Exception,), {}) for name in ('AuthenticationError', 'RateLimitError', 'APITimeoutError', 'APIConnectionError')})

    def test_supported_client_request(self):
        factory = MagicMock()
        client = factory.return_value.__enter__.return_value
        client.chat.completions.create.return_value = types.SimpleNamespace(choices=[types.SimpleNamespace(finish_reason='stop', message=types.SimpleNamespace(content=json.dumps(self.result)))])
        with patch.dict(sys.modules, openai=self.sdk()):
            result = review.analyse(self.cv, 'Analyst', 'Entry', 'SQL', 'fake', client_factory=factory)
        self.assertEqual(result, self.result)
        factory.assert_called_once_with(api_key='fake', timeout=30.0, max_retries=0)
        args = client.chat.completions.create.call_args.kwargs
        self.assertFalse(args['store'])
        self.assertEqual(json.loads(args['messages'][1]['content'])['cv'], self.cv)
        client.chat.completions.create.assert_called_once()

    def test_safe_provider_errors_no_retry(self):
        sdk = self.sdk()
        for name, message in [('AuthenticationError', 'credentials'), ('RateLimitError', 'limit'), ('APITimeoutError', 'timed out'), ('APIConnectionError', 'connect')]:
            factory = MagicMock()
            factory.return_value.__enter__.return_value.chat.completions.create.side_effect = getattr(sdk, name)('PRIVATE PAYLOAD')
            with patch.dict(sys.modules, openai=sdk), self.assertRaises(review.ReviewError) as caught:
                review.analyse(self.cv, 'Analyst', 'Entry', '', 'fake', client_factory=factory)
            self.assertIn(message, str(caught.exception))
            self.assertNotIn('PRIVATE', str(caught.exception))
            self.assertEqual(factory.return_value.__enter__.return_value.chat.completions.create.call_count, 1)

    def extract(self, text=None, pages=1, encrypted=False, corrupt=False, data=b'%PDF-synthetic'):
        doc = Mock()
        doc.needs_pass = encrypted
        doc.__len__ = Mock(return_value=pages)
        doc.__iter__ = Mock(return_value=iter([types.SimpleNamespace(get_text=lambda: text or '')]))
        opened = Mock()
        opened.return_value.__enter__ = Mock(return_value=doc)
        opened.return_value.__exit__ = Mock(return_value=False)
        if corrupt:
            opened.side_effect = RuntimeError('private filename')
        with patch.dict(sys.modules, pymupdf=types.SimpleNamespace(open=opened)):
            return review.extract_pdf(data)

    def test_pdf_text(self):
        self.assertEqual(self.extract(self.cv), self.cv)

    def test_pdf_failure_branches(self):
        for kwargs, message in [({'encrypted': True}, 'encrypted'), ({'pages':31}, '30 pages'), ({}, 'readable'), ({'text':'a'*24001}, '24,000'), ({'corrupt':True}, 'Unable'), ({'data':b'x'*(review.MAX_BYTES+1)}, '5 MB')]:
            with self.subTest(kwargs=list(kwargs)), self.assertRaisesRegex(review.ReviewError, message):
                self.extract(**kwargs)

if __name__ == '__main__':
    unittest.main()


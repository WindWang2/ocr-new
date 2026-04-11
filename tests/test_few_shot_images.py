
import unittest
from unittest.mock import MagicMock, patch
import os
import base64
import io
from PIL import Image
from instrument_reader import MultimodalModelReader, DynamicInstrumentLibrary

class TestFewShotImages(unittest.TestCase):
    def setUp(self):
        self.mock_provider = MagicMock()
        self.mock_provider.model_name = "test-model"
        self.mock_provider.chat.return_value = '{"test": "response"}'
        self.reader = MultimodalModelReader(provider=self.mock_provider)
        
        # Create a dummy image for testing
        self.test_image_path = "test_image.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(self.test_image_path)
        
        self.example_image_path = "example_image.jpg"
        img_ex = Image.new('RGB', (100, 100), color='blue')
        img_ex.save(self.example_image_path)

    def tearDown(self):
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)
        if os.path.exists(self.example_image_path):
            os.remove(self.example_image_path)

    @patch('instrument_reader.DynamicInstrumentLibrary.get_template')
    def test_analyze_image_with_examples(self, mock_get_template):
        # Setup mock template with example images
        mock_get_template.return_value = {
            'instrument_type': 'test_instrument',
            'example_images': [self.example_image_path]
        }
        
        prompt = "test prompt"
        self.reader.analyze_image(self.test_image_path, prompt, instrument_type="test_instrument")
        
        # Verify provider.chat was called
        self.assertTrue(self.mock_provider.chat.called)
        args, kwargs = self.mock_provider.chat.call_args
        
        # Check that images list contains 2 images (base + 1 example)
        images = kwargs.get('images')
        self.assertEqual(len(images), 2)
        
        # Verify base64 encoding (just check they are strings and not empty)
        for img_b64 in images:
            self.assertIsInstance(img_b64, str)
            self.assertTrue(len(img_b64) > 0)

    @patch('instrument_reader.DynamicInstrumentLibrary.get_template')
    def test_analyze_image_without_examples(self, mock_get_template):
        # Setup mock template without example images
        mock_get_template.return_value = {
            'instrument_type': 'test_instrument',
            'example_images': []
        }
        
        prompt = "test prompt"
        self.reader.analyze_image(self.test_image_path, prompt, instrument_type="test_instrument")
        
        # Verify provider.chat was called with 1 image
        images = self.mock_provider.chat.call_args[1].get('images')
        self.assertEqual(len(images), 1)

if __name__ == '__main__':
    unittest.main()

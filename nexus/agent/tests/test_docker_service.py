
import unittest
from unittest.mock import MagicMock, patch
import os
from docker.errors import DockerException
from nexus.agent.services.docker import DockerService

class TestDockerService(unittest.TestCase):
    def setUp(self):
        # Patch docker.from_env to avoid actual connection attempts during init
        self.patcher = patch('docker.from_env')
        self.mock_from_env = self.patcher.start()
        
    def tearDown(self):
        self.patcher.stop()

    @patch('nexus.agent.services.docker.docker.DockerClient')
    @patch('os.path.exists')
    def test_connect_socket_detection(self, mock_exists, mock_client_cls):
        # Simulate from_env failing with DockerException
        self.mock_from_env.side_effect = DockerException("Env connection failed")
        
        # Simulate socket existence
        def exists_side_effect(path):
            if path == "/run/user/1000/docker.sock":
                return True
            return False
        mock_exists.side_effect = exists_side_effect
        
        # Simulate DockerClient connection failure for the first socket, success for second
        def client_side_effect(*args, **kwargs):
            base_url = kwargs.get('base_url')
            if base_url == "unix:///var/run/docker.sock":
                raise DockerException("Socket not found")
            return MagicMock()
            
        mock_client_cls.side_effect = client_side_effect
        
        # Test connection
        service = DockerService()
        
        # Verify it attempted to connect to the user socket
        calls = mock_client_cls.call_args_list
        base_urls = [call.kwargs.get('base_url') for call in calls]
        
        self.assertIn("unix:///run/user/1000/docker.sock", base_urls)

    def test_get_container_description_oci(self):
        service = DockerService()
        container = MagicMock()
        container.labels = {"org.opencontainers.image.description": "OCI Description"}
        
        desc = service.get_container_description(container)
        self.assertEqual(desc, "OCI Description")

    def test_get_container_description_generic(self):
        service = DockerService()
        container = MagicMock()
        container.labels = {"description": "Generic Description"}
        
        desc = service.get_container_description(container)
        self.assertEqual(desc, "Generic Description")

    def test_get_container_description_compose(self):
        service = DockerService()
        container = MagicMock()
        container.labels = {"com.docker.compose.service": "web-service"}
        
        desc = service.get_container_description(container)
        self.assertEqual(desc, "Service: web-service")

    def test_get_container_description_fallback_image(self):
        service = DockerService()
        container = MagicMock()
        container.labels = {}
        container.image.tags = ["nginx:latest"]
        
        desc = service.get_container_description(container)
        self.assertEqual(desc, "nginx:latest")

if __name__ == '__main__':
    unittest.main()

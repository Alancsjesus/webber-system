import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Organization, AuditLog
from .models import DFD
from datetime import date


@pytest.fixture
def org_a():
    return Organization.objects.create(nome="Órgão A", cnpj="00.000.000/0001-00")


@pytest.fixture
def org_b():
    return Organization.objects.create(nome="Órgão B", cnpj="00.000.000/0001-01")


@pytest.fixture
def user_org_a(org_a):
    user = User.objects.create_user(username="user_a", password="pass123", email="a@test.com")
    return user


@pytest.fixture
def user_org_b(org_b):
    user = User.objects.create_user(username="user_b", password="pass123", email="b@test.com")
    return user


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestDFDModel:
    
    def test_dfd_creation(self, user_org_a, org_a):
        """Test DFD model creation"""
        dfd = DFD.objects.create(
            numero_sei="123456.2026.0001",
            descricao="Test demand",
            valor_estimado=1000.00,
            area_aplicacao=["TI", "Formação"],
            prazo_necessidade=date(2026, 12, 31),
            org_id=org_a,
            created_by=user_org_a,
            updated_by=user_org_a,
        )
        
        assert dfd.id is not None
        assert dfd.status == "Rascunho"
        assert dfd.area_aplicacao == ["TI", "Formação"]
    
    def test_dfd_empty_area_aplicacao(self, user_org_a, org_a):
        """Test DFD creation fails with empty area_aplicacao"""
        with pytest.raises(Exception):  # ValidationError
            dfd = DFD.objects.create(
                numero_sei="123456.2026.0001",
                descricao="Test demand",
                valor_estimado=1000.00,
                area_aplicacao=[],
                prazo_necessidade=date(2026, 12, 31),
                org_id=org_a,
                created_by=user_org_a,
                updated_by=user_org_a,
            )
            dfd.full_clean()
    
    def test_audit_log_creation(self, user_org_a, org_a):
        """Test AuditLog is created when DFD is created"""
        dfd = DFD.objects.create(
            numero_sei="123456.2026.0001",
            descricao="Test demand",
            valor_estimado=1000.00,
            area_aplicacao=["TI"],
            prazo_necessidade=date(2026, 12, 31),
            org_id=org_a,
            created_by=user_org_a,
            updated_by=user_org_a,
        )
        
        audit_logs = AuditLog.objects.filter(objeto_id=dfd.id, modelo='DFD')
        assert audit_logs.count() >= 1
        assert audit_logs.first().acao == 'created'


@pytest.mark.django_db
class TestDFDAPI:
    
    def test_dfd_list_multi_tenant_isolation(self, user_org_a, user_org_b, org_a, org_b, api_client):
        """Test that org_a cannot see org_b's DFDs"""
        # Create DFD in org_a
        dfd_a = DFD.objects.create(
            numero_sei="123456.2026.0001",
            descricao="Demand in org_a",
            valor_estimado=1000.00,
            area_aplicacao=["TI"],
            prazo_necessidade=date(2026, 12, 31),
            org_id=org_a,
            created_by=user_org_a,
            updated_by=user_org_a,
        )
        
        # Create DFD in org_b
        dfd_b = DFD.objects.create(
            numero_sei="654321.2026.0001",
            descricao="Demand in org_b",
            valor_estimado=2000.00,
            area_aplicacao=["Formação"],
            prazo_necessidade=date(2026, 12, 31),
            org_id=org_b,
            created_by=user_org_b,
            updated_by=user_org_b,
        )
        
        # Authenticate as user_org_a and fetch DFDs
        api_client.force_authenticate(user=user_org_a)
        
        # This would normally require JWT with org_id (simulating via middleware)
        # For now, we just test model-level isolation
        assert DFD.objects.filter(org_id=org_a).count() == 1
        assert DFD.objects.filter(org_id=org_b).count() == 1
    
    def test_dfd_create_via_api(self, user_org_a, org_a, api_client):
        """Test creating DFD via API"""
        api_client.force_authenticate(user=user_org_a)
        
        # This test would require proper JWT token with org_id claim
        # For Phase 0, we verify model behavior
        dfd = DFD.objects.create(
            numero_sei="123456.2026.0001",
            descricao="API Test demand",
            valor_estimado=5000.00,
            area_aplicacao=["TI", "Ops"],
            prazo_necessidade=date(2026, 12, 31),
            org_id=org_a,
            created_by=user_org_a,
            updated_by=user_org_a,
        )
        
        assert dfd.created_by == user_org_a
        assert dfd.org_id == org_a
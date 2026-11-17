import unittest
import json
from app import create_app, db
from app.models import Usuario, Tanque, Medicao, LimiteAlerta, Alerta
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class AquaWaterTechTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_ca01_cadastro_usuario(self):
        """CA01 / RF01: Cadastro com sucesso e rejeição de e-mail duplicado."""
        res = self.client.post('/cadastro', data={
            'nome': 'João Piscicultor',
            'email': 'joao@fazenda.com',
            'senha': 'senha123',
            'confirmacao': 'senha123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        user = Usuario.query.filter_by(email='joao@fazenda.com').first()
        self.assertIsNotNone(user)
        self.assertTrue(user.checar_senha('senha123'))

        # Tentativa com e-mail duplicado
        res_dup = self.client.post('/cadastro', data={
            'nome': 'Outro João',
            'email': 'joao@fazenda.com',
            'senha': 'outrasenha',
            'confirmacao': 'outrasenha'
        }, follow_redirects=True)
        self.assertIn('já está em uso'.encode('utf-8'), res_dup.data)

    def test_ca02_ca03_login_logout_sessao(self):
        """CA02 & CA03 / RF02 & RF03: Login correto, falha com senha errada e encerramento de sessão."""
        user = Usuario(nome='Maria', email='maria@agro.com', perfil='piscicultor')
        user.set_senha('segredo123')
        db.session.add(user)
        db.session.commit()

        # Login com senha errada
        res_err = self.client.post('/login', data={'email': 'maria@agro.com', 'senha': 'errada'}, follow_redirects=True)
        self.assertIn('E-mail ou senha incorretos'.encode('utf-8'), res_err.data)

        # Login correto
        res_ok = self.client.post('/login', data={'email': 'maria@agro.com', 'senha': 'segredo123'}, follow_redirects=True)
        self.assertIn('Bem-vindo'.encode('utf-8'), res_ok.data)

        # Logout
        res_out = self.client.get('/logout', follow_redirects=True)
        self.assertIn('Sessão encerrada'.encode('utf-8'), res_out.data)

        # Tentativa de acessar rota protegida sem sessão
        res_prot = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(res_prot.status_code, 302)
        self.assertIn('/login', res_prot.headers['Location'])

    def test_ca04_ca05_ca08_tanque_medicao_e_alertas(self):
        """CA04, CA05, CA08 / RF04, RF05, RF08: Criação de tanque, recepção de medição e disparo de alertas."""
        user = Usuario(nome='Carlos', email='carlos@piscicultura.com', perfil='piscicultor')
        user.set_senha('123456')
        db.session.add(user)
        db.session.commit()

        # Autentica Carlos
        self.client.post('/login', data={'email': 'carlos@piscicultura.com', 'senha': '123456'})

        # Cria tanque
        res_tanque = self.client.post('/tanques/novo', data={
            'nome': 'Tanque Alevinos',
            'descricao_local': 'Setor 1'
        }, follow_redirects=True)
        self.assertEqual(res_tanque.status_code, 200)

        tanque = Tanque.query.filter_by(nome='Tanque Alevinos').first()
        self.assertIsNotNone(tanque)
        self.assertEqual(tanque.usuario_id, user.id)

        # Envia medição crítica de oxigênio (OD = 2.5 mg/L < 4.0 mg/L) via API
        payload = {
            'tanque_id': tanque.id,
            'oxigenio_dissolvido': 2.5,
            'ph': 7.2,
            'temperatura': 28.0,
            'origem': 'sensor_esp32'
        }
        res_api = self.client.post('/api/medicoes',
                                   data=json.dumps(payload),
                                   content_type='application/json')
        self.assertEqual(res_api.status_code, 201)
        data = json.loads(res_api.data)
        self.assertEqual(data['status'], 'sucesso')
        self.assertTrue(len(data['alertas_gerados']) > 0)
        self.assertEqual(data['alertas_gerados'][0]['parametro'], 'oxigenio')

        # Verifica se o alerta foi persistido no banco
        alerta = Alerta.query.filter_by(tanque_id=tanque.id).first()
        self.assertIsNotNone(alerta)
        self.assertEqual(alerta.parametro, 'oxigenio')
        self.assertEqual(alerta.valor_observado, 2.5)

        # Testa inserção manual de teste via formulário web
        res_manual = self.client.post(f'/tanques/{tanque.id}/medicoes/nova', data={
            'oxigenio': '6.8',
            'ph': '7.4',
            'temperatura': '27.5'
        }, follow_redirects=True)
        self.assertEqual(res_manual.status_code, 200)
        self.assertIn('Medição registrada'.encode('utf-8'), res_manual.data)

        # Testa resolução do alerta
        res_res = self.client.post(f'/alertas/{alerta.id}/resolver', follow_redirects=True)
        self.assertEqual(res_res.status_code, 200)
        db.session.refresh(alerta)
        self.assertEqual(alerta.status, 'resolvido')

    def test_ca06_ca07_consulta_e_limites(self):
        """CA06 & CA07 / RF06 & RF07: Consulta de histórico e configuração de limites."""
        user = Usuario(nome='Ana', email='ana@fazenda.com', perfil='piscicultor')
        user.set_senha('123456')
        db.session.add(user)
        db.session.commit()

        tanque = Tanque(usuario_id=user.id, nome='Tanque Teste')
        db.session.add(tanque)
        db.session.commit()

        self.client.post('/login', data={'email': 'ana@fazenda.com', 'senha': '123456'})

        # Atualiza limites
        res_lim = self.client.post(f'/tanques/{tanque.id}/limites', data={
            'oxigenio_min': '5.0',
            'oxigenio_max': '10.0',
            'ph_min': '6.0',
            'ph_max': '8.0',
            'temperatura_min': '22.0',
            'temperatura_max': '30.0'
        }, follow_redirects=True)
        self.assertEqual(res_lim.status_code, 200)

        lim_ox = LimiteAlerta.query.filter_by(tanque_id=tanque.id, parametro='oxigenio').first()
        self.assertEqual(lim_ox.valor_minimo, 5.0)

        # Insere medições para consulta
        m1 = Medicao(tanque_id=tanque.id, oxigenio_dissolvido=6.0, ph=7.0, temperatura=25.0)
        db.session.add(m1)
        db.session.commit()

        # Consulta via API de histórico
        res_hist = self.client.get(f'/api/tanques/{tanque.id}/historico')
        self.assertEqual(res_hist.status_code, 200)
        dados = json.loads(res_hist.data)
        self.assertEqual(len(dados), 1)
        self.assertEqual(dados[0]['oxigenio_dissolvido'], 6.0)

    def test_ca09_isolamento_de_dados(self):
        """CA09 / RF09: Piscicultor A não pode acessar os dados do tanque do Piscicultor B."""
        user_a = Usuario(nome='User A', email='a@test.com', perfil='piscicultor')
        user_a.set_senha('123456')
        user_b = Usuario(nome='User B', email='b@test.com', perfil='piscicultor')
        user_b.set_senha('123456')
        db.session.add_all([user_a, user_b])
        db.session.commit()

        tanque_b = Tanque(usuario_id=user_b.id, nome='Tanque do B')
        db.session.add(tanque_b)
        db.session.commit()

        # Login como User A
        self.client.post('/login', data={'email': 'a@test.com', 'senha': '123456'})

        # Tenta acessar o tanque do B
        res = self.client.get(f'/tanques/{tanque_b.id}')
        self.assertEqual(res.status_code, 403)

        # Tenta acessar a área de administração sendo apenas piscicultor
        res_adm = self.client.get('/admin/usuarios')
        self.assertEqual(res_adm.status_code, 403)

    def test_ca10_administracao_desativar_usuario(self):
        """CA10 / RF10: Administrador pode listar e desativar contas de usuários."""
        admin = Usuario(nome='Admin', email='admin@aquatec.com', perfil='admin')
        admin.set_senha('adminpass')
        user = Usuario(nome='Comum', email='comum@aquatec.com', perfil='piscicultor', ativo=True)
        user.set_senha('userpass')
        db.session.add_all([admin, user])
        db.session.commit()

        # Login como Admin
        self.client.post('/login', data={'email': 'admin@aquatec.com', 'senha': 'adminpass'})

        # Desativa o usuário comum
        res = self.client.post(f'/admin/usuarios/{user.id}/toggle-status', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Recarrega o usuário do banco
        db.session.refresh(user)
        self.assertFalse(user.ativo)

        # Logout do admin
        self.client.get('/logout')

        # Usuário desativado não consegue logar
        res_login_inativo = self.client.post('/login', data={'email': 'comum@aquatec.com', 'senha': 'userpass'}, follow_redirects=True)
        self.assertIn('Esta conta foi desativada'.encode('utf-8'), res_login_inativo.data)

if __name__ == '__main__':
    unittest.main()

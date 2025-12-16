import pytest
import time
import statistics
import logging
from typing import List, Dict

# Importação dos serviços (ajuste os caminhos conforme sua estrutura de pastas)
from src.services.regex_service import RegexService
from src.services.ner_service import NERService
from src.services.local_llm_service import LocalLLMService

# Configuração básica de log para não poluir o output do teste
logging.basicConfig(level=logging.ERROR)

# --- DADOS DE TESTE (Fornecidos no Prompt) ---
RAW_DATA = [
    {
        "prompt_text": "Gostaria que você redigisse uma carta de advertência disciplinar formal, com tom sério mas respeitoso, para o colaborador Carlos Eduardo Souza, matrícula 9902-A. O documento deve citar que, apesar dos feedbacks anteriores, houve reincidência em atrasos injustificados e um episódio de desrespeito com a gerência. Para fins de registro, os dados do funcionário são: CPF 234.567.890-12 e RG 20.123.456-7. Ele ocupa o cargo de Analista de Suporte Pleno no departamento de Infraestrutura de TI. O incidente ocorreu na unidade onde ele está lotado, localizada na Rua da Consolação, 500, Consolação, São Paulo-SP, CEP 01302-000. É importante mencionar que esta advertência impacta seu histórico, pois ele já possui uma suspensão anterior por uso indevido de recursos da empresa. O salário atual dele é R$ 4.850,00 e qualquer desconto por faltas será aplicado na conta onde recebe (Banco Bradesco, agência 3456, conta 00123-4). Finalize solicitando a assinatura dele e do gestor imediato."
    },
    {
        "prompt_text": "Preciso criar um comunicado oficial para a diretoria informando a promoção da colaboradora Mariana Alves da Costa, que passará a atuar como Gerente de Projetos Sênior. O novo pacote de remuneração foi aprovado. O salário base passará para R$ 22.500,00 a partir do próximo mês. Ela continuará no departamento de Engenharia Civil, mas precisaremos atualizar os acessos do seu usuário de rede m.alves para o perfil administrativo (IP fixo atual: 10.0.20.15). Os dados pessoais para o contrato aditivo são: CPF 987.654.321-00, nascida em 20/10/1988. O endereço residencial dela mudou recentemente para: Avenida Boa Viagem, 2500, Boa Viagem, Recife-PE, CEP 51020-000. Seus contatos atualizados são o e-mail mariana.costa@corp.com e telefone (81) 99988-7766. Ressalte no texto que ela atingiu todas as metas do último ciclo."
    },
    {
        "prompt_text": "Por favor, analise os dados abaixo para gerar o termo de rescisão do colaborador Roberto Nunes Oliveira, matrícula 1020-BR. Ele está sendo desligado sem justa causa. Precisamos ter atenção aos descontos: ele possui um empréstimo consignado com saldo devedor de R$ 5.000,00 e uma penhora judicial de pensão alimentícia ativa em folha. Dados para o TRCT: CPF 333.444.555-66, RG 30.405.607-8. O último salário foi R$ 7.200,00. O pagamento das verbas deve ser creditado no Banco Santander, agência 0088, conta 77665-9. O endereço para envio do telegrama de notificação é Rua das Laranjeiras, 45, Laranjeiras, Rio de Janeiro-RJ, CEP 22240-000. Confirme se o e-mail pessoal roberto.nunes@provider.com é o correto para envio dos comprovantes."
    },
    {
        "prompt_text": "Estou encaminhando os dados da colaboradora Fernanda Lima Rocha para processamento de afastamento previdenciário. Ela apresentou um atestado de 30 dias. Diagnóstico sigiloso: a colaboradora foi diagnosticada com Burnout grave e início de depressão, necessitando de afastamento imediato do ambiente corporativo. Seguem os dados para agendamento de perícia: CPF 555.666.777-88, Data de Nascimento 12/03/1990. Cargo atual: Coordenadora de Vendas Regional no departamento Comercial. Contato para acompanhamento: telefone (31) 98877-6655. O endereço cadastrado para correspondência do INSS é Alameda das Rosas, 890, Setor Oeste, Goiânia-GO, CEP 74110-000. O login de rede f.rocha deve ser suspenso temporariamente durante o período de licença."
    },
    {
        "prompt_text": "Poderia redigir um e-mail de boas-vindas caloroso para o nosso novo contratado, Sr. Paulo Ricardo Martins? Ele iniciará conosco na próxima segunda-feira. No corpo do e-mail, inclua um resumo dos dados cadastrados para conferência dele. Nome completo: Paulo Ricardo Martins, CPF 111.222.333-44, RG 40.555.666-7. Ele ocupará o cargo de Desenvolvedor Full Stack Júnior no departamento de Tecnologia. O salário inicial acordado é R$ 6.500,00. Instrua-o a confirmar se a conta para depósito está correta: Banco do Brasil, agência 1122, conta 33445-6. O kit de trabalho (notebook e monitor) será entregue no endereço: Rua Sete de Setembro, 1500, Centro, Curitiba-PR, CEP 80020-000. Também informe que o usuário dele será p.martins e o IP da sua estação remota já foi configurado como 192.168.1.100. Mencione discretamente que o plano de saúde cobre a terapia para seu filho, conforme solicitado na entrevista (questão de problema pessoal familiar que ele trouxe)."
    },
    {
        "prompt_text": "Escreva um e-mail formal endereçado ao nosso contato na Unimed solicitando a inclusão urgente de um dependente no plano do colaborador Jeferson Mendes. No corpo do e-mail, organize os dados necessários para que eles possam emitir a carteirinha. O dependente é Lucas Mendes (filho), CPF 055.123.456-78, nascido em 05/02/2015. Especifique que o endereço para envio do cartão físico é diferente do titular: Rua das Acácias, 405, bloco B, Jardim Botânico, Porto Alegre-RS, CEP 90690-000. Peça para enviarem a confirmação para o e-mail corporativo do pai, j.mendes@empresa.com.br, assim que processado."
    },
    {
        "prompt_text": "Preciso redigir uma notificação formal de suspensão preventiva para a colaboradora Amanda Souza Oliveira. O texto deve informar que detectamos atividades irregulares vinculadas às credenciais dela. Para embasar o documento, cite tecnicamente que houve exfiltração de dados monitorada a partir do usuário de rede a.oliveira e do IP estático 172.16.10.45, alocados na estação de trabalho dela. Ela atua como Analista de BI no departamento de Inteligência de Mercado. O tom deve ser jurídico, mencionando que isso configura violação grave da política de confidencialidade, o que configura um histórico disciplinar de justa causa em potencial. Finalize dizendo que tentamos contato telefônico no número (21) 98888-1122 sem sucesso e que ela deve aguardar instruções."
    },
    {
        "prompt_text": "Atue como um especialista em Segurança do Trabalho. Com base nas anotações de campo abaixo, gere um texto narrativo, detalhado e técnico descrevendo o acidente para ser inserido no sistema da Previdência Social (CAT). Colaborador envolvido: Roberto Carlos da Silva (Matrícula 3040), RG 15.678.900-1 e CPF 222.333.444-55. Função: Eletricista de Manutenção. O texto deve descrever que o acidente ocorreu na Via Anchieta, km 12, Ipiranga, São Paulo-SP, onde ele sofreu fratura exposta no antebraço direito após queda de escada durante reparo de rotina. Mencione que o salário de contribuição é R$ 3.200,00 para fins de cálculo de auxílio."
    },
    {
        "prompt_text": "Gere uma carta formal de retratação e esclarecimento financeiro para a Diretora Claudia Ferraz. Explique educadamente que identificamos a falha no pagamento do bônus de performance de R$ 50.000,00 referente ao Q3 e que o valor já foi programado para transferência. O texto deve confirmar que o depósito será feito na conta cadastrada: Banco Safra, agência 0090, conta corrente 12345-6. Para fins de conferência fiscal no recibo que ela receberá por e-mail (claudia.ferraz@executiva.com), cite que o CPF vinculado ao pagamento é 999.888.777-66. Tranquilize-a dizendo que o salário base mensal de R$ 35.000,00 não sofrerá alterações."
    },
    {
        "prompt_text": "Estou elaborando o aditivo de transferência para o colaborador Felipe Araújo Costa. Por favor, gere o texto da cláusula de 'Do Local de Trabalho' e 'Da Qualificação' com base nos novos dados. Ele passará a exercer o cargo de Supervisor de Logística Pleno no departamento de Operações Nordeste. O texto deve declarar que o empregado passa a residir no seguinte endereço para todos os fins legais: Avenida Santos Dumont, 1200, Aldeota, Fortaleza-CE, CEP 60150-160. Mantenha o telefone (85) 99123-4567 como contato de emergência na ficha de qualificação."
    },
]

# --- FIXTURES ---


@pytest.fixture(scope="module")
def prompts():
    """Retorna apenas a lista de textos dos prompts."""
    return [item["prompt_text"] for item in RAW_DATA]


@pytest.fixture(scope="module")
def services():
    """Inicializa os serviços uma única vez para o módulo de teste."""
    print("\n\n[SETUP] Inicializando Serviços (Carregando Modelos)...")

    start_setup = time.perf_counter()
    try:
        regex = RegexService()
        ner = NERService()  # Pode demorar alguns segundos para carregar o spaCy
        llm = LocalLLMService()  # Conecta ao Ollama
    except Exception as e:
        pytest.fail(f"Falha ao inicializar serviços: {e}")

    end_setup = time.perf_counter()
    print(f"[SETUP] Serviços carregados em {end_setup - start_setup:.2f}s")

    return {"regex": regex, "ner": ner, "llm": llm}


# --- TESTS ---


def test_performance_benchmark(prompts, services):
    """
    Roda os 10 prompts em cada serviço e no pipeline completo, medindo o tempo.
    """
    regex_service = services["regex"]
    ner_service = services["ner"]
    llm_service = services["llm"]

    # Dicionários para armazenar tempos (em segundos)
    times = {"Regex": [], "NER": [], "LLM": [], "Full_Pipeline": []}

    print(f"\n{'='*20} INICIANDO BENCHMARK ({len(prompts)} prompts) {'='*20}")

    for i, prompt in enumerate(prompts, 1):
        print(f"Processando Prompt {i}/{len(prompts)}...", end=" ", flush=True)

        # 1. Teste Regex Isolado
        t0 = time.perf_counter()
        regex_text, regex_map = regex_service.filter_by_regex(prompt)
        t1 = time.perf_counter()
        times["Regex"].append(t1 - t0)

        # 2. Teste NER Isolado (No texto cru)
        # Nota: Testamos no texto cru para ver a performance pura do NER,
        # mas no pipeline ele recebe o texto filtrado.
        t0 = time.perf_counter()
        ner_service.filter_by_ner(prompt)
        t1 = time.perf_counter()
        times["NER"].append(t1 - t0)

        # 3. Teste LLM Isolado (No texto cru)
        t0 = time.perf_counter()
        llm_service.filter_sensitive_topics(prompt)
        t1 = time.perf_counter()
        times["LLM"].append(t1 - t0)

        # 4. Teste Pipeline Integrado (Fluxo Real Sequencial)
        # O tempo aqui inclui a lógica de passar o texto de um para o outro
        t0 = time.perf_counter()

        # Passo A: Regex
        p_text_1, p_map_1 = regex_service.filter_by_regex(prompt)
        p_placeholders_1 = [m.placeholder for m in p_map_1]

        # Passo B: NER (Recebe texto do Regex e lista de placeholders existentes)
        p_text_2, p_map_2 = ner_service.filter_by_ner(
            p_text_1, existing_placeholders=p_placeholders_1
        )
        p_placeholders_2 = [m.placeholder for m in p_map_2]
        all_placeholders = p_placeholders_1 + p_placeholders_2

        # Passo C: LLM (Recebe texto do NER e lista acumulada de placeholders)
        # Nota: O LLM é geralmente o gargalo.
        llm_service.filter_sensitive_topics(
            p_text_2, existing_placeholders=all_placeholders
        )

        t1 = time.perf_counter()
        times["Full_Pipeline"].append(t1 - t0)

        print("OK")

    # --- RELATÓRIO FINAL ---
    print(f"\n\n{'='*60}")
    print(f"{'SERVIÇO':<15} | {'MÉDIA (s)':<10} | {'MÍN (s)':<10} | {'MÁX (s)':<10}")
    print(f"{'-'*60}")

    for service_name, time_list in times.items():
        avg_time = statistics.mean(time_list)
        min_time = min(time_list)
        max_time = max(time_list)
        print(
            f"{service_name:<15} | {avg_time:<10.4f} | {min_time:<10.4f} | {max_time:<10.4f}"
        )

    print(f"{'='*60}\n")

    # Asserções básicas para garantir que o teste não falhe silenciosamente se algo for instantâneo (erro)
    assert statistics.mean(times["Full_Pipeline"]) > 0
    # O pipeline completo deve ser logicamente mais lento que o Regex sozinho
    assert statistics.mean(times["Full_Pipeline"]) > statistics.mean(times["Regex"])

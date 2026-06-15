from playwright.sync_api import sync_playwright
import time
import re

# Principais cidades por estado (top cidades para maximizar cobertura)
CIDADES_POR_ESTADO = {
    "AC": ["Rio Branco", "Cruzeiro do Sul", "Sena Madureira"],
    "AL": ["Maceió", "Arapiraca", "Palmeira dos Índios", "Rio Largo"],
    "AP": ["Macapá", "Santana", "Laranjal do Jari"],
    "AM": ["Manaus", "Parintins", "Itacoatiara", "Manacapuru"],
    "BA": ["Salvador", "Feira de Santana", "Vitória da Conquista", "Camaçari", "Itabuna", "Juazeiro", "Ilhéus", "Barreiras"],
    "CE": ["Fortaleza", "Caucaia", "Juazeiro do Norte", "Maracanaú", "Sobral", "Crato"],
    "DF": ["Brasília", "Taguatinga", "Ceilândia", "Samambaia", "Planaltina"],
    "ES": ["Vitória", "Serra", "Vila Velha", "Cariacica", "Cachoeiro de Itapemirim", "Linhares"],
    "GO": ["Goiânia", "Aparecida de Goiânia", "Anápolis", "Rio Verde", "Luziânia"],
    "MA": ["São Luís", "Imperatriz", "Timon", "Caxias", "Codó"],
    "MT": ["Cuiabá", "Várzea Grande", "Rondonópolis", "Sinop", "Tangará da Serra"],
    "MS": ["Campo Grande", "Dourados", "Três Lagoas", "Corumbá", "Ponta Porã"],
    "MG": ["Belo Horizonte", "Uberlândia", "Contagem", "Juiz de Fora", "Betim", "Montes Claros", "Uberaba", "Governador Valadares", "Ipatinga"],
    "PA": ["Belém", "Ananindeua", "Santarém", "Marabá", "Castanhal"],
    "PB": ["João Pessoa", "Campina Grande", "Santa Rita", "Patos"],
    "PR": ["Curitiba", "Londrina", "Maringá", "Ponta Grossa", "Cascavel", "São José dos Pinhais", "Foz do Iguaçu", "Colombo", "Guarapuava", "Paranaguá"],
    "PE": ["Recife", "Caruaru", "Olinda", "Petrolina", "Paulista", "Jaboatão dos Guararapes"],
    "PI": ["Teresina", "Parnaíba", "Picos", "Floriano"],
    "RJ": ["Rio de Janeiro", "São Gonçalo", "Duque de Caxias", "Nova Iguaçu", "Niterói", "Belford Roxo", "Campos dos Goytacazes", "Petrópolis"],
    "RN": ["Natal", "Mossoró", "Parnamirim", "São Gonçalo do Amarante"],
    "RS": ["Porto Alegre", "Caxias do Sul", "Pelotas", "Canoas", "Santa Maria", "Gravataí", "Viamão", "Novo Hamburgo", "São Leopoldo"],
    "RO": ["Porto Velho", "Ji-Paraná", "Ariquemes", "Cacoal"],
    "RR": ["Boa Vista", "Rorainópolis", "Caracaraí"],
    "SC": ["Florianópolis", "Joinville", "Blumenau", "São José", "Criciúma", "Chapecó", "Itajaí", "Lages"],
    "SP": ["São Paulo", "Campinas", "São Bernardo do Campo", "Santo André", "Guarulhos", "Osasco", "Ribeirão Preto", "Sorocaba", "Mauá", "São José dos Campos", "Santos", "Mogi das Cruzes", "Bauru", "Piracicaba"],
    "SE": ["Aracaju", "Nossa Senhora do Socorro", "Lagarto", "Itabaiana"],
    "TO": ["Palmas", "Araguaína", "Gurupi", "Porto Nacional"],
}


def buscar_no_google_maps(termo: str, limite: int = 20, estado: str = None, cidade: str = None) -> list[dict]:
    """
    Busca estabelecimentos no Google Maps.
    - Se tem cidade: busca direto "termo em Cidade UF"
    - Se tem só estado (sem cidade): percorre as principais cidades do estado
    - Se não tem nada: busca o termo direto
    """
    if cidade:
        # Busca específica por cidade
        termo_completo = f"{termo} em {cidade}"
        if estado:
            termo_completo += f" {estado}"
        print(f"[CIDADE] Buscando direto: {termo_completo}")
        return _buscar_termo(termo_completo, limite)
    elif estado and estado.upper() in CIDADES_POR_ESTADO:
        # Só percorre o estado se não tiver cidade
        return _buscar_por_estado(termo, limite, estado.upper())
    return _buscar_termo(termo, limite)


def _buscar_por_estado(termo: str, limite: int, estado: str) -> list[dict]:
    """Percorre cidades do estado até atingir o limite."""
    cidades = CIDADES_POR_ESTADO.get(estado, [])
    todos = []
    nomes_vistos = set()
    por_cidade = max(20, limite // max(len(cidades), 1) + 10)

    for cidade in cidades:
        if len(todos) >= limite:
            break
        termo_completo = f"{termo} em {cidade} {estado}"
        print(f"[ESTADO] Buscando: {termo_completo}")
        try:
            parcial = _buscar_termo(termo_completo, por_cidade)
            novos = 0
            for emp in parcial:
                chave = emp["nome"].strip().lower()
                if chave not in nomes_vistos:
                    nomes_vistos.add(chave)
                    emp["_cidade_busca"] = cidade
                    emp["_estado"] = estado
                    todos.append(emp)
                    novos += 1
                    if len(todos) >= limite:
                        break
            print(f"[ESTADO] {cidade}: +{novos} novos (total {len(todos)})")
        except Exception as e:
            print(f"[ERRO] {cidade}: {e}")
        time.sleep(1)

    return todos[:limite]


def _buscar_termo(termo: str, limite: int = 20) -> list[dict]:
    """Faz scraping do Google Maps para um termo específico."""
    resultados = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
                "--no-zygote",
                "--disable-software-rasterizer",
            ]
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="pt-BR",
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        url = f"https://www.google.com/maps/search/{termo.replace(' ', '+')}"
        print(f"[INFO] Acessando: {url}")
        page.goto(url, wait_until="networkidle", timeout=30000)
        time.sleep(2)

        lista_seletor = 'div[role="feed"]'
        try:
            page.wait_for_selector(lista_seletor, timeout=10000)
        except Exception:
            print("[AVISO] Lista de resultados não encontrada.")
            browser.close()
            return []

        # Scroll progressivo
        print(f"[INFO] Carregando até {limite} resultados via scroll...")
        ultima_contagem = 0
        tentativas_sem_novos = 0

        while True:
            cards = page.query_selector_all('div[role="feed"] > div > div > a')
            contagem_atual = len(cards)
            if contagem_atual >= limite:
                break
            if contagem_atual == ultima_contagem:
                tentativas_sem_novos += 1
                if tentativas_sem_novos >= 4:
                    print(f"[INFO] Sem novos após scroll. Total: {contagem_atual}")
                    break
            else:
                tentativas_sem_novos = 0
            ultima_contagem = contagem_atual
            page.eval_on_selector(lista_seletor, "el => el.scrollBy(0, 2000)")
            time.sleep(1.2)

        cards = page.query_selector_all('div[role="feed"] > div > div')
        print(f"[INFO] Extraindo {min(len(cards), limite)} cards...")
        vistos = set()

        for card in cards:
            if len(resultados) >= limite:
                break
            try:
                nome = ""
                link_el = card.query_selector('a[href*="/maps/place/"]')
                if link_el:
                    nome = (link_el.get_attribute("aria-label") or "").strip()
                if not nome or nome in vistos:
                    continue
                vistos.add(nome)

                link_maps = link_el.get_attribute("href") or "" if link_el else ""
                textos = card.query_selector_all('div.lI9IFe span.OSrXXb, div.UaQhfb span, div.W4Efsd span')
                todos_textos = []
                for t in textos:
                    txt = t.inner_text().strip()
                    if txt and txt not in todos_textos:
                        todos_textos.append(txt)

                endereco = _extrair_endereco(todos_textos)
                telefone = _extrair_telefone(todos_textos)
                categoria = _extrair_categoria(todos_textos, endereco, telefone)

                resultados.append({
                    "nome": nome,
                    "categoria": categoria,
                    "endereco": endereco,
                    "cidade": _extrair_cidade(endereco),
                    "telefone": telefone,
                    "link_maps": link_maps,
                })
                print(f"[OK] {len(resultados)}. {nome} | {telefone} | {endereco}")
            except Exception as e:
                print(f"[ERRO] {e}")

        browser.close()
    return resultados


def _extrair_telefone(textos):
    for t in textos:
        if re.search(r'\(?\d{2}\)?\s?\d{4,5}[-\s]?\d{4}', t):
            return t
    return ""

def _extrair_endereco(textos):
    for t in textos:
        if re.search(r'\d', t) and len(t) > 8:
            if any(p in t.lower() for p in ['rua', 'av', 'r.', 'alameda', 'estrada', 'rod', ',', 'n°', 'nº']):
                return t
    for t in textos:
        if re.search(r'\d', t) and len(t) > 10:
            return t
    return ""

def _extrair_cidade(endereco):
    if not endereco:
        return ""
    endereco_limpo = re.sub(r'\d{5}-\d{3}', '', endereco).strip(' ,')
    m = re.search(r'-\s*([^,\-]+?)\s*[-,]\s*[A-Z]{2}\b', endereco_limpo)
    if m:
        return m.group(1).strip()
    m = re.search(r',\s*([^,\-]+?)\s*-\s*[A-Z]{2}\b', endereco_limpo)
    if m:
        return m.group(1).strip()
    partes = [p.strip() for p in endereco_limpo.split(',')]
    for parte in reversed(partes):
        parte_limpa = re.sub(r'\s*-\s*[A-Z]{2}$', '', parte).strip()
        if parte_limpa and not re.match(r'^\d+$', parte_limpa) and len(parte_limpa) > 2:
            return parte_limpa
    return ""

def _extrair_categoria(textos, endereco, telefone):
    for t in textos:
        if t == endereco or t == telefone:
            continue
        if t in ['·', '•', '–', '-', '']:
            continue
        if len(t) < 40 and not re.search(r'\d', t):
            return t
    return ""

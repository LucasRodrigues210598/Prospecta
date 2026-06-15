# 🗺️ Google Maps Scraper API

API local gratuita em Python para buscar empresas, endereços e telefones no Google Maps.

---

## 📦 Instalação

### 1. Pré-requisitos
- Python 3.10 ou superior instalado
- pip atualizado

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Instalar o navegador do Playwright

```bash
playwright install chromium
```

---

## ▶️ Rodando a API

```bash
python main.py
```

A API ficará disponível em: **http://localhost:8000**

---

## 🔍 Como usar

### Endpoint principal

```
GET http://localhost:8000/buscar?termo=pizzarias+em+Maringá&limite=10
```

### Parâmetros

| Parâmetro | Tipo   | Obrigatório | Descrição                          |
|-----------|--------|-------------|-----------------------------------|
| `termo`   | string | ✅ Sim      | O que buscar (ex: "padarias em Londrina") |
| `limite`  | int    | ❌ Não      | Qtd de resultados (padrão: 10, máx: 50) |

### Exemplo de resposta

```json
{
  "termo": "pizzarias em Maringá",
  "total": 3,
  "resultados": [
    {
      "nome": "Pizzaria Bella Napoli",
      "categoria": "Pizzaria",
      "endereco": "Av. Brasil, 1234 - Maringá, PR",
      "telefone": "(44) 3333-4444",
      "link_maps": "https://www.google.com/maps/place/..."
    }
  ]
}
```

---

## 🌐 Testando no navegador

Acesse a documentação interativa (Swagger):

```
http://localhost:8000/docs
```

---

## 💡 Exemplos de termos de busca

- `restaurantes em Curitiba`
- `academias em São Paulo zona sul`
- `dentistas em Nova Londrina PR`
- `hoteis em Foz do Iguaçu`
- `supermercados em Londrina`

---

## ⚠️ Dicas importantes

- **Velocidade**: cada resultado leva ~2-3 segundos para extrair. 10 resultados ≈ 30 segundos.
- **Bloqueios**: para uso intenso (centenas de buscas/dia), considere usar proxies.
- **Uso pessoal**: para volumes baixos/médios funciona sem proxy.

---

## 🔗 Integrar na sua plataforma

Basta fazer uma requisição HTTP GET para a API:

```javascript
// JavaScript / Fetch
const response = await fetch('http://localhost:8000/buscar?termo=pizzarias+em+Maringa&limite=10');
const data = await response.json();
console.log(data.resultados);
```

```python
# Python / requests
import requests
resp = requests.get('http://localhost:8000/buscar', params={'termo': 'pizzarias em Maringá', 'limite': 10})
print(resp.json())
```

```php
// PHP
$data = file_get_contents('http://localhost:8000/buscar?termo=pizzarias+em+Maringa&limite=10');
$json = json_decode($data, true);
print_r($json['resultados']);
```

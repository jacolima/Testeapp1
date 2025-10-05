from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import database

app = Flask(__name__)
# Configura o CORS para permitir requisições do seu frontend
CORS(app)

@app.route('/')
def index():
    """Serve a página principal da aplicação."""
    return render_template('index.html')

# --- Endpoints do Dashboard e Transações ---

@app.route('/api/dashboard_data', methods=['GET'])
def get_dashboard_data():
    """Endpoint para fornecer os dados do dashboard."""
    dados = database.get_dados_dashboard()
    return jsonify(dados)

@app.route('/api/categorias', methods=['GET'])
def get_categorias():
    """Endpoint para buscar as categorias por tipo."""
    tipo = request.args.get('tipo')
    if not tipo or tipo not in ['Receita', 'Despesa']:
        return jsonify({"error": "Tipo inválido"}), 400
    
    categorias = database.get_categorias(tipo)
    return jsonify(categorias)

@app.route('/api/transacao', methods=['POST'])
def add_transacao():
    """Endpoint para adicionar uma nova transação."""
    data = request.json
    try:
        tipo = data['tipo']
        descricao = data['descricao']
        valor = data['valor']
        categoria_id = data['categoria_id']
        data_vencimento = data.get('data_vencimento', None)
        success, message = database.inserir_transacao(tipo, descricao, valor, categoria_id, data_vencimento)
        if success:
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "message": message}), 400
    except KeyError as e:
        return jsonify({"success": False, "message": f"Campo em falta: {e}"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/transacoes', methods=['GET'])
def get_transacoes_endpoint():
    """Endpoint para buscar transações para o extrato, com filtro opcional."""
    tipo_filtro = request.args.get('tipo', None)
    transacoes = database.get_transacoes(tipo_filtro=tipo_filtro)
    return jsonify(transacoes)

# --- Endpoints de Dívidas ---

@app.route('/api/dividas', methods=['GET'])
def get_dividas():
    dividas = database.get_dividas()
    return jsonify(dividas)

@app.route('/api/divida', methods=['POST'])
def add_divida():
    data = request.json
    success, message = database.inserir_divida(data['descricao'], data['valor_total'])
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400

@app.route('/api/divida/<int:divida_id>', methods=['DELETE'])
def delete_divida(divida_id):
    success, message = database.remover_divida(divida_id)
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400
        
# --- Endpoints de Investimentos ---

@app.route('/api/investimentos', methods=['GET'])
def get_investimentos():
    investimentos = database.get_investimentos()
    return jsonify(investimentos)

@app.route('/api/investimento', methods=['POST'])
def add_investimento():
    data = request.json
    success, message = database.inserir_investimento(data['ativo'], data['valor_atual'])
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400

@app.route('/api/investimento/<int:investimento_id>', methods=['DELETE'])
def delete_investimento(investimento_id):
    success, message = database.remover_investimento(investimento_id)
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400

if __name__ == '__main__':
    # Garante que as tabelas sejam criadas ao iniciar o servidor
    database.criar_tabelas()
    app.run(host='0.0.0.0', port=5000, debug=True)
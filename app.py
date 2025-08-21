from flask import Flask, request, jsonify
from instagrapi import Client
import os
import logging
import time

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Configurações
INSTAGRAM_USER = "testemidazn8n"
INSTAGRAM_PASS = "testemidaz123"

# Cliente Instagram global
instagram_client = None
last_login_time = 0

def get_instagram_client():
    global instagram_client, last_login_time
    current_time = time.time()
    
    # Relogin a cada 2 horas para manter sessão ativa
    if instagram_client is None or (current_time - last_login_time) > 7200:
        try:
            instagram_client = Client()
            instagram_client.login(INSTAGRAM_USER, INSTAGRAM_PASS)
            last_login_time = current_time
            logging.info("Login no Instagram realizado com sucesso")
        except Exception as e:
            logging.error(f"Erro no login Instagram: {e}")
            raise e
    
    return instagram_client

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy", 
        "service": "instagram-automation",
        "version": "1.0.0"
    })

@app.route('/add-close-friend', methods=['POST'])
def add_close_friend():
    try:
        data = request.get_json()
        
        if not data or 'username' not in data:
            return jsonify({
                "success": False, 
                "error": "Username é obrigatório"
            }), 400
            
        username = data['username'].replace('@', '').strip().lower()
        
        if not username:
            return jsonify({
                "success": False, 
                "error": "Username inválido"
            }), 400
            
        # Conecta no Instagram
        cl = get_instagram_client()
        
        # Busca o usuário
        user_info = cl.user_info_by_username(username)
        user_id = user_info.pk
        
        # Adiciona aos close friends
        cl.user_add_to_close_friends(user_id)
        
        logging.info(f"Usuário @{username} (ID: {user_id}) adicionado aos close friends")
        
        return jsonify({
            "success": True,
            "message": f"@{username} adicionado aos close friends",
            "user_id": str(user_id),
            "user_full_name": user_info.full_name
        })
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Erro ao adicionar close friend: {error_msg}")
        
        # Tratamento de erros específicos
        if "User not found" in error_msg:
            return jsonify({
                "success": False,
                "error": "Usuário do Instagram não encontrado"
            }), 404
        elif "challenge_required" in error_msg:
            return jsonify({
                "success": False,
                "error": "Instagram solicitou verificação. Verifique a conta manualmente."
            }), 429
        else:
            return jsonify({
                "success": False,
                "error": f"Erro interno: {error_msg}"
            }), 500

@app.route('/check-user', methods=['POST'])
def check_user():
    """Endpoint para verificar se um usuário existe no Instagram"""
    try:
        data = request.get_json()
        username = data['username'].replace('@', '').strip().lower()
        
        cl = get_instagram_client()
        user_info = cl.user_info_by_username(username)
        
        return jsonify({
            "success": True,
            "exists": True,
            "user_id": str(user_info.pk),
            "username": user_info.username,
            "full_name": user_info.full_name,
            "is_private": user_info.is_private
        })
        
    except Exception as e:
        return jsonify({
            "success": True,
            "exists": False,
            "error": str(e)
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
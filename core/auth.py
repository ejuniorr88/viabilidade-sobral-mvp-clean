def handle_oauth_callback() -> None:
    error = safe_get_query_param("error")
    error_description = safe_get_query_param("error_description")
    code = safe_get_query_param("code")

    if error:
        clear_user_in_state()
        st.session_state["auth_message"] = (
            f"Erro no login Google: {error}"
            + (f" — {error_description}" if error_description else "")
        )
        clear_auth_query_params()
        return

    # 1) Só faz o exchange quando realmente voltou do Google com ?code=
    if code:
        last_code = st.session_state.get("last_oauth_code")
        if last_code == code:
            return

        supabase = get_supabase_auth_client()

        try:
            result = supabase.auth.exchange_code_for_session({"auth_code": code})

            user_obj = getattr(result, "user", None)
            session_obj = getattr(result, "session", None)

            if user_obj is None and isinstance(result, dict):
                user_obj = result.get("user")
                session_obj = result.get("session")

            if user_obj is None and session_obj is not None:
                user_obj = getattr(session_obj, "user", None)
                if user_obj is None and isinstance(session_obj, dict):
                    user_obj = session_obj.get("user")

            if user_obj is not None:
                store_user_in_state(user_obj)
                st.session_state["last_oauth_code"] = code
                st.session_state["auth_message"] = "Login efetuado com sucesso."
            else:
                clear_user_in_state()
                st.session_state["auth_message"] = "Não foi possível concluir o login Google."

            clear_auth_query_params()
            st.rerun()
            return

        except Exception as e:
            clear_user_in_state()
            st.session_state["auth_message"] = f"Erro ao concluir o login Google: {e}"
            clear_auth_query_params()
            return

    # 2) Se já temos usuário salvo no session_state, NÃO bate no Auth de novo
    if st.session_state.get("auth_logged_in") and st.session_state.get("auth_user_id"):
        return

    # 3) Só tenta sincronizar com rede se a UI ainda não tiver sessão local
    sync_user_from_current_session()

def start_google_login(force_select_account: bool = False) -> Optional[str]:
    supabase = get_supabase_auth_client()
    redirect_to = build_auth_callback_url()

    options = {
        "redirect_to": redirect_to,
    }

    if force_select_account:
        options["queryParams"] = {
            "prompt": "select_account",
        }

    try:
        response = supabase.auth.sign_in_with_oauth(
            {
                "provider": "google",
                "options": options,
            }
        )

        if hasattr(response, "url"):
            url = response.url
        elif isinstance(response, dict):
            url = response.get("url")
        else:
            url = None

        _push_auth_debug(
            "start_google_login",
            {
                "redirect_to": redirect_to,
                "has_url": bool(url),
                "force_select_account": force_select_account,
            },
        )
        return url

    except Exception as e:
        st.session_state["auth_message"] = f"Erro ao iniciar login Google: {e}"
        _push_auth_debug("start_google_login_exception", {"error": str(e)})
        return None

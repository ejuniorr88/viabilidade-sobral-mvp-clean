                "Original": row.get("original_amount") or 0,
                "Desconto": row.get("discount_amount") or 0,
                "Final": row.get("final_amount") or 0,
                "Status": row.get("payment_status") or "—",
                "Confirmado em": _fmt_dt(row.get("confirmed_at") or row.get("created_at")),
            }
        )

    st.dataframe(report_rows, use_container_width=True, hide_index=True)


def render_coupons_admin_section(*, current_user_email: str) -> None:
    st.markdown("### Gestão interna de cupons")

    if not user_can_manage_coupons(current_user_email):
        st.info("Seu usuário não tem permissão para gerir cupons.")
        return

    configured = st.secrets.get("COUPONS_ADMIN_EMAILS", "")
    if not configured:
        st.warning(
            "COUPONS_ADMIN_EMAILS não está configurado nos secrets. "
            "Em modo provisório, o usuário logado atual pode acessar esta área."
        )

    st.markdown("#### Criar novo cupom")
    _render_coupon_form(mode="create")

    rows = list_coupon_codes(limit=100)
    _render_coupon_list(rows)
    _render_coupon_usage_report()

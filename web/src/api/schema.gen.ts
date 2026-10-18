/**
 * Generated from handoff/openapi.json by scripts/gen-api.mjs — do not edit by hand.
 */

export type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };

export interface paths {
    "/api/v1/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Health Check */
        get: operations["health_check_api_v1_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/signup": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Signup */
        post: operations["signup_api_v1_auth_signup_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Login */
        post: operations["login_api_v1_auth_login_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/refresh": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Refresh Tokens */
        post: operations["refresh_tokens_api_v1_auth_refresh_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/logout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Logout */
        post: operations["logout_api_v1_auth_logout_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/me/organizations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List My Organizations
         * @description Organizations the caller is an active member of, sorted by name.
         *     Clients call this after login to pick the active organization.
         */
        get: operations["list_my_organizations_api_v1_me_organizations_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/members": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Members
         * @description The team: active members first, then removed ones (kept so past records
         *     can still show who did the work). Use the active ones for "performed by"
         *     pickers on shared devices.
         */
        get: operations["list_members_api_v1_organizations__organization_id__members_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/invites": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Invite */
        post: operations["create_invite_api_v1_organizations__organization_id__invites_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/invites/{token}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Preview Invite */
        get: operations["preview_invite_api_v1_invites__token__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/invites/{token}/accept": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Accept Invite */
        post: operations["accept_invite_api_v1_invites__token__accept_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/products": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Products */
        get: operations["list_products_api_v1_organizations__organization_id__products_get"];
        put?: never;
        /** Create Product */
        post: operations["create_product_api_v1_organizations__organization_id__products_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/products/{product_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Product */
        get: operations["get_product_api_v1_organizations__organization_id__products__product_id__get"];
        put?: never;
        post?: never;
        /** Delete Product */
        delete: operations["delete_product_api_v1_organizations__organization_id__products__product_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/products/{product_id}/checklist-items": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Checklist Items */
        get: operations["list_checklist_items_api_v1_organizations__organization_id__products__product_id__checklist_items_get"];
        put?: never;
        /** Add Checklist Item */
        post: operations["add_checklist_item_api_v1_organizations__organization_id__products__product_id__checklist_items_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/products/{product_id}/checklist-items/{item_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Remove Checklist Item */
        delete: operations["remove_checklist_item_api_v1_organizations__organization_id__products__product_id__checklist_items__item_id__delete"];
        options?: never;
        head?: never;
        /** Update Checklist Item */
        patch: operations["update_checklist_item_api_v1_organizations__organization_id__products__product_id__checklist_items__item_id__patch"];
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/products/{product_id}/batches": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Product Batches */
        get: operations["list_product_batches_api_v1_organizations__organization_id__products__product_id__batches_get"];
        put?: never;
        /** Record Batch */
        post: operations["record_batch_api_v1_organizations__organization_id__products__product_id__batches_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/batches/{batch_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Batch */
        get: operations["get_batch_api_v1_organizations__organization_id__batches__batch_id__get"];
        put?: never;
        post?: never;
        /** Delete Batch */
        delete: operations["delete_batch_api_v1_organizations__organization_id__batches__batch_id__delete"];
        options?: never;
        head?: never;
        /** Edit Batch */
        patch: operations["edit_batch_api_v1_organizations__organization_id__batches__batch_id__patch"];
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/batches/{batch_id}/history": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Batch History */
        get: operations["get_batch_history_api_v1_organizations__organization_id__batches__batch_id__history_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/attachments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Upload Attachment */
        post: operations["upload_attachment_api_v1_organizations__organization_id__attachments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/attachments/{attachment_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Download Attachment */
        get: operations["download_attachment_api_v1_organizations__organization_id__attachments__attachment_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/equipment": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Equipment */
        get: operations["list_equipment_api_v1_organizations__organization_id__equipment_get"];
        put?: never;
        /** Create Equipment */
        post: operations["create_equipment_api_v1_organizations__organization_id__equipment_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/equipment/{equipment_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Equipment */
        get: operations["get_equipment_api_v1_organizations__organization_id__equipment__equipment_id__get"];
        put?: never;
        post?: never;
        /** Delete Equipment */
        delete: operations["delete_equipment_api_v1_organizations__organization_id__equipment__equipment_id__delete"];
        options?: never;
        head?: never;
        /** Update Equipment */
        patch: operations["update_equipment_api_v1_organizations__organization_id__equipment__equipment_id__patch"];
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/equipment/{equipment_id}/attachment": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Attach Document */
        post: operations["attach_document_api_v1_organizations__organization_id__equipment__equipment_id__attachment_post"];
        /** Detach Document */
        delete: operations["detach_document_api_v1_organizations__organization_id__equipment__equipment_id__attachment_delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/chemicals": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Chemicals */
        get: operations["list_chemicals_api_v1_organizations__organization_id__chemicals_get"];
        put?: never;
        /** Create Chemical */
        post: operations["create_chemical_api_v1_organizations__organization_id__chemicals_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/chemicals/{chemical_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Chemical */
        delete: operations["delete_chemical_api_v1_organizations__organization_id__chemicals__chemical_id__delete"];
        options?: never;
        head?: never;
        /** Update Chemical */
        patch: operations["update_chemical_api_v1_organizations__organization_id__chemicals__chemical_id__patch"];
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/chemicals/{chemical_id}/attachment": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Attach Chemical Document */
        post: operations["attach_chemical_document_api_v1_organizations__organization_id__chemicals__chemical_id__attachment_post"];
        /** Detach Chemical Document */
        delete: operations["detach_chemical_document_api_v1_organizations__organization_id__chemicals__chemical_id__attachment_delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/waste-types": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Waste Types */
        get: operations["list_waste_types_api_v1_organizations__organization_id__waste_types_get"];
        put?: never;
        /** Create Waste Type */
        post: operations["create_waste_type_api_v1_organizations__organization_id__waste_types_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/waste-types/{waste_type_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Waste Type */
        delete: operations["delete_waste_type_api_v1_organizations__organization_id__waste_types__waste_type_id__delete"];
        options?: never;
        head?: never;
        /** Update Waste Type */
        patch: operations["update_waste_type_api_v1_organizations__organization_id__waste_types__waste_type_id__patch"];
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/medical-checks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Medical Checks */
        get: operations["list_medical_checks_api_v1_organizations__organization_id__medical_checks_get"];
        put?: never;
        /** Create Medical Check */
        post: operations["create_medical_check_api_v1_organizations__organization_id__medical_checks_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/medical-checks/{medical_check_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Medical Check */
        delete: operations["delete_medical_check_api_v1_organizations__organization_id__medical_checks__medical_check_id__delete"];
        options?: never;
        head?: never;
        /** Update Medical Check */
        patch: operations["update_medical_check_api_v1_organizations__organization_id__medical_checks__medical_check_id__patch"];
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/allergens": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Allergens */
        get: operations["list_allergens_api_v1_organizations__organization_id__allergens_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/allergens/{allergen_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Allergen Presence */
        patch: operations["update_allergen_presence_api_v1_organizations__organization_id__allergens__allergen_id__patch"];
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/event-log-types": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Event Log Types */
        get: operations["list_event_log_types_api_v1_organizations__organization_id__event_log_types_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/event-log-types/{event_log_type_id}/entries": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Event Entries */
        get: operations["list_event_entries_api_v1_organizations__organization_id__event_log_types__event_log_type_id__entries_get"];
        put?: never;
        /** Record Event Entry */
        post: operations["record_event_entry_api_v1_organizations__organization_id__event_log_types__event_log_type_id__entries_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/event-entries/{entry_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Event Entry */
        delete: operations["delete_event_entry_api_v1_organizations__organization_id__event_entries__entry_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/controls/{period}/checklist-items": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Control Checklist Items */
        get: operations["list_control_checklist_items_api_v1_organizations__organization_id__controls__period__checklist_items_get"];
        put?: never;
        /** Add Control Checklist Item */
        post: operations["add_control_checklist_item_api_v1_organizations__organization_id__controls__period__checklist_items_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/controls/{period}/checklist-items/{item_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Remove Control Checklist Item */
        delete: operations["remove_control_checklist_item_api_v1_organizations__organization_id__controls__period__checklist_items__item_id__delete"];
        options?: never;
        head?: never;
        /** Update Control Checklist Item */
        patch: operations["update_control_checklist_item_api_v1_organizations__organization_id__controls__period__checklist_items__item_id__patch"];
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/controls/{period}/current": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Current Control */
        get: operations["get_current_control_api_v1_organizations__organization_id__controls__period__current_get"];
        /** Upsert Current Control */
        put: operations["upsert_current_control_api_v1_organizations__organization_id__controls__period__current_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/controls/{period}/records": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Control Records */
        get: operations["list_control_records_api_v1_organizations__organization_id__controls__period__records_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/control-records/{record_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Control Record */
        get: operations["get_control_record_api_v1_organizations__organization_id__control_records__record_id__get"];
        put?: never;
        post?: never;
        /** Delete Control Record */
        delete: operations["delete_control_record_api_v1_organizations__organization_id__control_records__record_id__delete"];
        options?: never;
        head?: never;
        /** Edit Control Record */
        patch: operations["edit_control_record_api_v1_organizations__organization_id__control_records__record_id__patch"];
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/control-records/{record_id}/history": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Control Record History */
        get: operations["get_control_record_history_api_v1_organizations__organization_id__control_records__record_id__history_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/controls/{period}/sheet": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Control Sheet */
        get: operations["get_control_sheet_api_v1_organizations__organization_id__controls__period__sheet_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/controls/{period}/items/{item_id}/check": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Check Control Item */
        post: operations["check_control_item_api_v1_organizations__organization_id__controls__period__items__item_id__check_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/control-records/{record_id}/submit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit Control Record */
        post: operations["submit_control_record_api_v1_organizations__organization_id__control_records__record_id__submit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/control-records/{record_id}/audit-events": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Control Audit Events */
        get: operations["list_control_audit_events_api_v1_organizations__organization_id__control_records__record_id__audit_events_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/dashboard": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Dashboard */
        get: operations["get_dashboard_api_v1_organizations__organization_id__dashboard_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/organizations/{organization_id}/setup-progress": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Setup Progress */
        get: operations["get_setup_progress_api_v1_organizations__organization_id__setup_progress_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** AllergenPresenceUpdateRequest */
        AllergenPresenceUpdateRequest: {
            /** Present */
            present: boolean;
        };
        /** AllergenStatusResponse */
        AllergenStatusResponse: {
            /**
             * Allergen Id
             * Format: uuid
             */
            allergen_id: string;
            /** Name */
            name: string;
            /** Position */
            position: number;
            /** Present */
            present: boolean;
        };
        /** AttachDocumentRequest */
        AttachDocumentRequest: {
            /**
             * Attachment Id
             * Format: uuid
             */
            attachment_id: string;
        };
        /** AttachmentResponse */
        AttachmentResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Filename */
            filename: string;
            /** Content Type */
            content_type: string;
            /** Size Bytes */
            size_bytes: number;
            /**
             * Uploaded By User Id
             * Format: uuid
             */
            uploaded_by_user_id: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** AttentionItemResponse */
        AttentionItemResponse: {
            /** Label */
            label: string;
            /** Severity */
            severity: string;
            /** Days */
            days: number;
        };
        /** AuditEventPageResponse */
        AuditEventPageResponse: {
            /** Items */
            items: components["schemas"]["AuditEventResponse"][];
            /**
             * Next Cursor
             * @description Pass as `cursor` to get the next (older) page. Null on the last page.
             */
            next_cursor: string | null;
        };
        /** AuditEventResponse */
        AuditEventResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Seq */
            seq: number;
            event_type: components["schemas"]["ControlAuditEventType"];
            /** Control Checklist Item Id */
            control_checklist_item_id: string | null;
            /** Item Label */
            item_label: string | null;
            /** Item Unit */
            item_unit: string | null;
            /**
             * Numeric Value
             * @description Numeric items: the reading recorded.
             */
            numeric_value: number | null;
            previous_status: components["schemas"]["ControlItemStatus"] | null;
            new_status: components["schemas"]["ControlItemStatus"] | null;
            /** Corrective Action */
            corrective_action: string | null;
            /** Amendment Reason */
            amendment_reason: string | null;
            actor: components["schemas"]["UserRefResponse"];
            performed_by: components["schemas"]["UserRefResponse"];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** AuthResponse */
        AuthResponse: {
            user: components["schemas"]["UserResponse"];
            tokens: components["schemas"]["TokenResponse"];
            /** Organization Id */
            organization_id?: string | null;
        };
        /** BatchAnswerInput */
        BatchAnswerInput: {
            /**
             * Checklist Item Id
             * Format: uuid
             */
            checklist_item_id: string;
            /** Answer */
            answer: boolean;
        };
        /** BatchAnswerResponse */
        BatchAnswerResponse: {
            /**
             * Checklist Item Id
             * Format: uuid
             */
            checklist_item_id: string;
            /** Answer */
            answer: boolean;
        };
        /** BatchCreateRequest */
        BatchCreateRequest: {
            /** Number */
            number: string;
            /** Name */
            name?: string | null;
            /**
             * Production Date
             * Format: date
             */
            production_date: string;
            /** Answers */
            answers: components["schemas"]["BatchAnswerInput"][];
            /** Deviation Note */
            deviation_note?: string | null;
            /** Corrective Action */
            corrective_action?: string | null;
            /**
             * Performed By User Id
             * @description Who physically made / checked the batch, on a shared device. Must be an active member. Defaults to the signed-in user (always recorded as signatory).
             */
            performed_by_user_id?: string | null;
        };
        /** BatchHistoryResponse */
        BatchHistoryResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Snapshot */
            snapshot: {
                [key: string]: components["schemas"]["JSONValue-Output"];
            };
            /**
             * Edited By User Id
             * Format: uuid
             */
            edited_by_user_id: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** BatchResponse */
        BatchResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Product Id
             * Format: uuid
             */
            product_id: string;
            /** Number */
            number: string;
            /** Name */
            name: string | null;
            /**
             * Production Date
             * Format: date
             */
            production_date: string;
            /** Has Deviation */
            has_deviation: boolean;
            /** Deviation Note */
            deviation_note: string | null;
            /** Corrective Action */
            corrective_action: string | null;
            /**
             * Signatory User Id
             * Format: uuid
             * @description The signed-in account that saved it.
             */
            signatory_user_id: string;
            /**
             * Performed By User Id
             * Format: uuid
             * @description Who physically did it.
             */
            performed_by_user_id: string;
            /** Answers */
            answers: components["schemas"]["BatchAnswerResponse"][];
        };
        /** BatchUpdateRequest */
        BatchUpdateRequest: {
            /** Number */
            number?: string | null;
            /** Name */
            name?: string | null;
            /** Production Date */
            production_date?: string | null;
            /** Answers */
            answers?: components["schemas"]["BatchAnswerInput"][] | null;
            /** Deviation Note */
            deviation_note?: string | null;
            /** Corrective Action */
            corrective_action?: string | null;
        };
        /** Body_upload_attachment_api_v1_organizations__organization_id__attachments_post */
        Body_upload_attachment_api_v1_organizations__organization_id__attachments_post: {
            /** File */
            file: string;
        };
        /** ChecklistItemCreateRequest */
        ChecklistItemCreateRequest: {
            /** Label */
            label: string;
        };
        /** ChecklistItemResponse */
        ChecklistItemResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Product Id
             * Format: uuid
             */
            product_id: string;
            /** Label */
            label: string;
            /** Position */
            position: number;
        };
        /** ChecklistItemUpdateRequest */
        ChecklistItemUpdateRequest: {
            /** Label */
            label: string;
        };
        /**
         * ChemicalCategory
         * @enum {string}
         */
        ChemicalCategory: "cleaning" | "disinfecting";
        /** ChemicalCreateRequest */
        ChemicalCreateRequest: {
            /** Name */
            name: string;
            category: components["schemas"]["ChemicalCategory"];
        };
        /** ChemicalResponse */
        ChemicalResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Organization Id
             * Format: uuid
             */
            organization_id: string;
            /** Name */
            name: string;
            category: components["schemas"]["ChemicalCategory"];
            /** Attachment Id */
            attachment_id: string | null;
        };
        /** ChemicalUpdateRequest */
        ChemicalUpdateRequest: {
            /** Name */
            name?: string | null;
            category?: components["schemas"]["ChemicalCategory"] | null;
        };
        /** ControlAnswerInput */
        ControlAnswerInput: {
            /**
             * Control Checklist Item Id
             * Format: uuid
             */
            control_checklist_item_id: string;
            /** Answer */
            answer: boolean;
        };
        /** ControlAnswerResponse */
        ControlAnswerResponse: {
            /**
             * Control Checklist Item Id
             * Format: uuid
             */
            control_checklist_item_id: string;
            /** Answer */
            answer: boolean;
            /** Numeric Value */
            numeric_value?: number | null;
        };
        /**
         * ControlAuditEventType
         * @enum {string}
         */
        ControlAuditEventType: "item_checked" | "item_amended" | "record_submitted";
        /** ControlChecklistItemCreateRequest */
        ControlChecklistItemCreateRequest: {
            /** Label */
            label: string;
            /**
             * @description `bool`: Так/Ні, «Ні» is the deviation. `numeric`: a measured value, outside [min_value, max_value] is the deviation. Fixed after creation.
             * @default bool
             */
            item_type: components["schemas"]["ControlItemType"];
            /**
             * Unit
             * @description Numeric items only, required (e.g. `°C`).
             */
            unit?: string | null;
            /**
             * Min Value
             * @description Numeric items: lowest safe value (inclusive).
             */
            min_value?: number | string | null;
            /**
             * Max Value
             * @description Numeric items: highest safe value (inclusive).
             */
            max_value?: number | string | null;
        };
        /** ControlChecklistItemResponse */
        ControlChecklistItemResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            period: components["schemas"]["ControlPeriod"];
            /** Label */
            label: string;
            /** Position */
            position: number;
            item_type: components["schemas"]["ControlItemType"];
            /** Unit */
            unit: string | null;
            /** Min Value */
            min_value: number | null;
            /** Max Value */
            max_value: number | null;
        };
        /**
         * ControlChecklistItemUpdateRequest
         * @description Partial update. Send only what changes; send `null` to open a bound.
         *     The item type cannot change.
         */
        ControlChecklistItemUpdateRequest: {
            /** Label */
            label?: string | null;
            /** Unit */
            unit?: string | null;
            /** Min Value */
            min_value?: number | string | null;
            /** Max Value */
            max_value?: number | string | null;
        };
        /**
         * ControlItemStatus
         * @enum {string}
         */
        ControlItemStatus: "pending" | "pass" | "deviation";
        /**
         * ControlItemType
         * @enum {string}
         */
        ControlItemType: "bool" | "numeric";
        /**
         * ControlPeriod
         * @enum {string}
         */
        ControlPeriod: "daily" | "monthly";
        /** ControlRecordHistoryResponse */
        ControlRecordHistoryResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Snapshot */
            snapshot: {
                [key: string]: components["schemas"]["JSONValue-Output"];
            };
            /**
             * Edited By User Id
             * Format: uuid
             */
            edited_by_user_id: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** ControlRecordResponse */
        ControlRecordResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            period: components["schemas"]["ControlPeriod"];
            /**
             * Period Date
             * Format: date
             */
            period_date: string;
            /**
             * Signatory User Id
             * Format: uuid
             */
            signatory_user_id: string;
            /** Has Deviation */
            has_deviation: boolean;
            /** Note */
            note: string | null;
            /** Answers */
            answers: components["schemas"]["ControlAnswerResponse"][];
        };
        /**
         * ControlRecordStatus
         * @description `draft` while items are being checked one by one; `submitted` once
         *     finalized. After submission, item changes are amendments that require a
         *     reason and are logged as `item_amended`.
         * @enum {string}
         */
        ControlRecordStatus: "draft" | "submitted";
        /** ControlRecordUpsertRequest */
        ControlRecordUpsertRequest: {
            /** Answers */
            answers: components["schemas"]["ControlAnswerInput"][];
            /**
             * Period Date
             * @description Day (or, for monthly controls, any day within the month) being filled in. Defaults to today in the organization's timezone. Cannot be in the future.
             */
            period_date?: string | null;
            /** Note */
            note?: string | null;
        };
        /** ControlSheetResponse */
        ControlSheetResponse: {
            /**
             * Record Id
             * @description Null until the first item is checked.
             */
            record_id: string | null;
            period: components["schemas"]["ControlPeriod"];
            /**
             * Period Date
             * Format: date
             */
            period_date: string;
            status: components["schemas"]["ControlRecordStatus"] | null;
            /** Has Deviation */
            has_deviation: boolean;
            /** Note */
            note: string | null;
            /** Submitted At */
            submitted_at: string | null;
            submitted_by: components["schemas"]["UserRefResponse"] | null;
            /** Items */
            items: components["schemas"]["SheetItemResponse"][];
        };
        /** ControlStatusResponse */
        ControlStatusResponse: {
            /** Filled */
            filled: boolean;
            /** Has Deviation */
            has_deviation: boolean | null;
        };
        /** DashboardResponse */
        DashboardResponse: {
            daily_control: components["schemas"]["ControlStatusResponse"];
            monthly_control: components["schemas"]["ControlStatusResponse"];
            /** Batches This Month */
            batches_this_month: number;
            /** Attention Items */
            attention_items: components["schemas"]["AttentionItemResponse"][];
        };
        /** EquipmentCreateRequest */
        EquipmentCreateRequest: {
            type: components["schemas"]["EquipmentType"];
            /** Name */
            name: string;
            /** Frequency */
            frequency: string;
            /**
             * Amount
             * @default 1
             */
            amount: number;
            /**
             * Affects Product Safety
             * @default false
             */
            affects_product_safety: boolean;
        };
        /** EquipmentResponse */
        EquipmentResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Organization Id
             * Format: uuid
             */
            organization_id: string;
            type: components["schemas"]["EquipmentType"];
            /** Name */
            name: string;
            /** Frequency */
            frequency: string;
            /** Amount */
            amount: number;
            /** Affects Product Safety */
            affects_product_safety: boolean;
            /** Attachment Id */
            attachment_id: string | null;
        };
        /**
         * EquipmentType
         * @enum {string}
         */
        EquipmentType: "production" | "refrigeration" | "measuring" | "other";
        /** EquipmentUpdateRequest */
        EquipmentUpdateRequest: {
            type?: components["schemas"]["EquipmentType"] | null;
            /** Name */
            name?: string | null;
            /** Frequency */
            frequency?: string | null;
            /** Amount */
            amount?: number | null;
            /** Affects Product Safety */
            affects_product_safety?: boolean | null;
        };
        /** EventEntryCreateRequest */
        EventEntryCreateRequest: {
            /**
             * Entry Date
             * Format: date
             */
            entry_date: string;
            /** Payload */
            payload: {
                [key: string]: components["schemas"]["JSONValue-Input"];
            };
            /**
             * Performed By User Id
             * @description Who physically did it, on a shared device. Must be an active member. Defaults to the signed-in user (always recorded as `responsible_user_id`).
             */
            performed_by_user_id?: string | null;
        };
        /** EventEntryResponse */
        EventEntryResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Event Log Type Id
             * Format: uuid
             */
            event_log_type_id: string;
            /**
             * Entry Date
             * Format: date
             */
            entry_date: string;
            /**
             * Responsible User Id
             * Format: uuid
             * @description The signed-in account that saved it.
             */
            responsible_user_id: string;
            /**
             * Performed By User Id
             * Format: uuid
             * @description Who physically did it.
             */
            performed_by_user_id: string;
            /** Payload */
            payload: {
                [key: string]: components["schemas"]["JSONValue-Output"];
            };
            /** Has Deviation */
            has_deviation: boolean;
        };
        /**
         * EventLogSchema
         * @enum {string}
         */
        EventLogSchema: "standard" | "water" | "pests";
        /** EventLogTypeResponse */
        EventLogTypeResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Key */
            key: string;
            /** Name */
            name: string;
            log_schema: components["schemas"]["EventLogSchema"];
            /** Icon Label */
            icon_label: string;
            /** Position */
            position: number;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** InviteAcceptRequest */
        InviteAcceptRequest: {
            /** Password */
            password?: string | null;
            /** Full Name */
            full_name?: string | null;
        };
        /** InviteCreateRequest */
        InviteCreateRequest: {
            /**
             * Email
             * Format: email
             */
            email: string;
            role: components["schemas"]["MembershipRole"];
        };
        /** InvitePreviewResponse */
        InvitePreviewResponse: {
            /** Organization Name */
            organization_name: string;
            /** Email */
            email: string;
            role: components["schemas"]["MembershipRole"];
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
        };
        /** InviteResponse */
        InviteResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Organization Id
             * Format: uuid
             */
            organization_id: string;
            /** Email */
            email: string;
            role: components["schemas"]["MembershipRole"];
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
        };
        /** ItemCheckRequest */
        ItemCheckRequest: {
            /**
             * Status
             * @description Required for Yes/No items. Ignored for numeric items: the server judges `value` against the item's range.
             */
            status?: ("pass" | "deviation") | null;
            /**
             * Value
             * @description Required for numeric items (the measured reading); not allowed for Yes/No items. Outside the range = `deviation`, which needs a corrective action.
             */
            value?: number | string | null;
            /**
             * Corrective Action
             * @description Required (min 3 characters) when status is `deviation`; ignored for `pass`.
             */
            corrective_action?: string | null;
            /**
             * Amendment Reason
             * @description Required (min 3 characters) when the record is already submitted.
             */
            amendment_reason?: string | null;
            /**
             * Performed By User Id
             * @description Who physically did the check, on a shared device. Must be an active member. Defaults to the signed-in user, who is always recorded as well.
             */
            performed_by_user_id?: string | null;
            /**
             * Period Date
             * @description Day (or any day within the month) to check. Defaults to the current period in the organization's timezone. Cannot be in the future.
             */
            period_date?: string | null;
        };
        "JSONValue-Input": JsonValue;
        "JSONValue-Output": JsonValue;
        /** LoginRequest */
        LoginRequest: {
            /**
             * Email
             * Format: email
             */
            email: string;
            /** Password */
            password: string;
        };
        /** LogoutRequest */
        LogoutRequest: {
            /** Refresh Token */
            refresh_token: string;
        };
        /** MedicalCheckCreateRequest */
        MedicalCheckCreateRequest: {
            /** Employee Name */
            employee_name: string;
            /**
             * Next Check Date
             * Format: date
             */
            next_check_date: string;
        };
        /** MedicalCheckResponse */
        MedicalCheckResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Organization Id
             * Format: uuid
             */
            organization_id: string;
            /** Employee Name */
            employee_name: string;
            /**
             * Next Check Date
             * Format: date
             */
            next_check_date: string;
        };
        /** MedicalCheckUpdateRequest */
        MedicalCheckUpdateRequest: {
            /** Employee Name */
            employee_name?: string | null;
            /** Next Check Date */
            next_check_date?: string | null;
        };
        /** MemberResponse */
        MemberResponse: {
            /**
             * User Id
             * Format: uuid
             */
            user_id: string;
            /** Full Name */
            full_name: string;
            role: components["schemas"]["MembershipRole"];
            /** Title */
            title: string | null;
            status: components["schemas"]["MembershipStatus"];
        };
        /**
         * MembershipRole
         * @enum {string}
         */
        MembershipRole: "owner" | "manager" | "staff";
        /**
         * MembershipStatus
         * @enum {string}
         */
        MembershipStatus: "active" | "removed";
        /** MyOrganizationResponse */
        MyOrganizationResponse: {
            /**
             * Organization Id
             * Format: uuid
             */
            organization_id: string;
            /** Name */
            name: string;
            /** Role */
            role: string;
            /** Title */
            title: string | null;
        };
        /** ProductCreateRequest */
        ProductCreateRequest: {
            /** Name */
            name: string;
        };
        /** ProductResponse */
        ProductResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Organization Id
             * Format: uuid
             */
            organization_id: string;
            /** Name */
            name: string;
        };
        /** RefreshRequest */
        RefreshRequest: {
            /** Refresh Token */
            refresh_token: string;
        };
        /** SetupProgressResponse */
        SetupProgressResponse: {
            /** Completed */
            completed: number;
            /** Total */
            total: number;
            /** Steps */
            steps: components["schemas"]["SetupStepResponse"][];
        };
        /** SetupStepResponse */
        SetupStepResponse: {
            /** Key */
            key: string;
            /** Label */
            label: string;
            /** Done */
            done: boolean;
            /** Count */
            count: number;
        };
        /** SheetItemResponse */
        SheetItemResponse: {
            /**
             * Control Checklist Item Id
             * Format: uuid
             */
            control_checklist_item_id: string;
            /** Label */
            label: string;
            /** Position */
            position: number;
            item_type: components["schemas"]["ControlItemType"];
            /** Unit */
            unit: string | null;
            /**
             * Min Value
             * @description Numeric items: the limits the current value was judged against (the item's current limits until it is first measured).
             */
            min_value: number | null;
            /** Max Value */
            max_value: number | null;
            /**
             * Value
             * @description Numeric items: the recorded reading.
             */
            value: number | null;
            status: components["schemas"]["ControlItemStatus"];
            /** Corrective Action */
            corrective_action: string | null;
            /** @description The signed-in account that saved it. */
            checked_by: components["schemas"]["UserRefResponse"] | null;
            /** @description Who physically did the check. */
            performed_by: components["schemas"]["UserRefResponse"] | null;
            /** Checked At */
            checked_at: string | null;
        };
        /** SignupRequest */
        SignupRequest: {
            /**
             * Email
             * Format: email
             */
            email: string;
            /** Password */
            password: string;
            /** Full Name */
            full_name: string;
            /** Organization Name */
            organization_name: string;
            /**
             * Timezone
             * @description IANA timezone of the venue, e.g. `Europe/Kyiv`. Decides when its day (and daily control sheet) starts.
             * @default UTC
             */
            timezone: string;
        };
        /** TokenResponse */
        TokenResponse: {
            /** Access Token */
            access_token: string;
            /** Refresh Token */
            refresh_token: string;
            /**
             * Token Type
             * @default bearer
             */
            token_type: string;
        };
        /** UserRefResponse */
        UserRefResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Full Name */
            full_name: string;
        };
        /** UserResponse */
        UserResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Email */
            email: string;
            /** Full Name */
            full_name: string;
        };
        /** ValidationError */
        ValidationError: {
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
            /** Input */
            input?: unknown;
            /** Context */
            ctx?: Record<string, never>;
        };
        /** WasteTypeCreateRequest */
        WasteTypeCreateRequest: {
            /** Name */
            name: string;
            /** Disposal Method */
            disposal_method: string;
        };
        /** WasteTypeResponse */
        WasteTypeResponse: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Organization Id
             * Format: uuid
             */
            organization_id: string;
            /** Name */
            name: string;
            /** Disposal Method */
            disposal_method: string;
        };
        /** WasteTypeUpdateRequest */
        WasteTypeUpdateRequest: {
            /** Name */
            name?: string | null;
            /** Disposal Method */
            disposal_method?: string | null;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    health_check_api_v1_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string;
                    };
                };
            };
        };
    };
    signup_api_v1_auth_signup_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SignupRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    login_api_v1_auth_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LoginRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    refresh_tokens_api_v1_auth_refresh_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RefreshRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TokenResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    logout_api_v1_auth_logout_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LogoutRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_my_organizations_api_v1_me_organizations_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MyOrganizationResponse"][];
                };
            };
        };
    };
    list_members_api_v1_organizations__organization_id__members_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MemberResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_invite_api_v1_organizations__organization_id__invites_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InviteCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InviteResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    preview_invite_api_v1_invites__token__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                token: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InvitePreviewResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    accept_invite_api_v1_invites__token__accept_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                token: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InviteAcceptRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_products_api_v1_organizations__organization_id__products_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProductResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_product_api_v1_organizations__organization_id__products_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProductCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProductResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_product_api_v1_organizations__organization_id__products__product_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                product_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProductResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_product_api_v1_organizations__organization_id__products__product_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                product_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_checklist_items_api_v1_organizations__organization_id__products__product_id__checklist_items_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                product_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChecklistItemResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    add_checklist_item_api_v1_organizations__organization_id__products__product_id__checklist_items_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                product_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ChecklistItemCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChecklistItemResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    remove_checklist_item_api_v1_organizations__organization_id__products__product_id__checklist_items__item_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                product_id: string;
                item_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_checklist_item_api_v1_organizations__organization_id__products__product_id__checklist_items__item_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                product_id: string;
                item_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ChecklistItemUpdateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChecklistItemResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_product_batches_api_v1_organizations__organization_id__products__product_id__batches_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                product_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BatchResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    record_batch_api_v1_organizations__organization_id__products__product_id__batches_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                product_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BatchCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BatchResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_batch_api_v1_organizations__organization_id__batches__batch_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                batch_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BatchResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_batch_api_v1_organizations__organization_id__batches__batch_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                batch_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    edit_batch_api_v1_organizations__organization_id__batches__batch_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                batch_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BatchUpdateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BatchResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_batch_history_api_v1_organizations__organization_id__batches__batch_id__history_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                batch_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BatchHistoryResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    upload_attachment_api_v1_organizations__organization_id__attachments_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_upload_attachment_api_v1_organizations__organization_id__attachments_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AttachmentResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    download_attachment_api_v1_organizations__organization_id__attachments__attachment_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                attachment_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_equipment_api_v1_organizations__organization_id__equipment_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EquipmentResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_equipment_api_v1_organizations__organization_id__equipment_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EquipmentCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EquipmentResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_equipment_api_v1_organizations__organization_id__equipment__equipment_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                equipment_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EquipmentResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_equipment_api_v1_organizations__organization_id__equipment__equipment_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                equipment_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_equipment_api_v1_organizations__organization_id__equipment__equipment_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                equipment_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EquipmentUpdateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EquipmentResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    attach_document_api_v1_organizations__organization_id__equipment__equipment_id__attachment_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                equipment_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AttachDocumentRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EquipmentResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    detach_document_api_v1_organizations__organization_id__equipment__equipment_id__attachment_delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                equipment_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EquipmentResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_chemicals_api_v1_organizations__organization_id__chemicals_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChemicalResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_chemical_api_v1_organizations__organization_id__chemicals_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ChemicalCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChemicalResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_chemical_api_v1_organizations__organization_id__chemicals__chemical_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                chemical_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_chemical_api_v1_organizations__organization_id__chemicals__chemical_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                chemical_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ChemicalUpdateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChemicalResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    attach_chemical_document_api_v1_organizations__organization_id__chemicals__chemical_id__attachment_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                chemical_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AttachDocumentRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChemicalResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    detach_chemical_document_api_v1_organizations__organization_id__chemicals__chemical_id__attachment_delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                chemical_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChemicalResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_waste_types_api_v1_organizations__organization_id__waste_types_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WasteTypeResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_waste_type_api_v1_organizations__organization_id__waste_types_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["WasteTypeCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WasteTypeResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_waste_type_api_v1_organizations__organization_id__waste_types__waste_type_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                waste_type_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_waste_type_api_v1_organizations__organization_id__waste_types__waste_type_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                waste_type_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["WasteTypeUpdateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WasteTypeResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_medical_checks_api_v1_organizations__organization_id__medical_checks_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MedicalCheckResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_medical_check_api_v1_organizations__organization_id__medical_checks_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MedicalCheckCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MedicalCheckResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_medical_check_api_v1_organizations__organization_id__medical_checks__medical_check_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                medical_check_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_medical_check_api_v1_organizations__organization_id__medical_checks__medical_check_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                medical_check_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MedicalCheckUpdateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MedicalCheckResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_allergens_api_v1_organizations__organization_id__allergens_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AllergenStatusResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_allergen_presence_api_v1_organizations__organization_id__allergens__allergen_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                allergen_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AllergenPresenceUpdateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AllergenStatusResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_event_log_types_api_v1_organizations__organization_id__event_log_types_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EventLogTypeResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_event_entries_api_v1_organizations__organization_id__event_log_types__event_log_type_id__entries_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                event_log_type_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EventEntryResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    record_event_entry_api_v1_organizations__organization_id__event_log_types__event_log_type_id__entries_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                event_log_type_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EventEntryCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EventEntryResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_event_entry_api_v1_organizations__organization_id__event_entries__entry_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                entry_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_control_checklist_items_api_v1_organizations__organization_id__controls__period__checklist_items_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                period: components["schemas"]["ControlPeriod"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ControlChecklistItemResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    add_control_checklist_item_api_v1_organizations__organization_id__controls__period__checklist_items_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                period: components["schemas"]["ControlPeriod"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ControlChecklistItemCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ControlChecklistItemResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    remove_control_checklist_item_api_v1_organizations__organization_id__controls__period__checklist_items__item_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                period: components["schemas"]["ControlPeriod"];
                item_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_control_checklist_item_api_v1_organizations__organization_id__controls__period__checklist_items__item_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                period: components["schemas"]["ControlPeriod"];
                item_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ControlChecklistItemUpdateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ControlChecklistItemResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_current_control_api_v1_organizations__organization_id__controls__period__current_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                period: components["schemas"]["ControlPeriod"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ControlRecordResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    upsert_current_control_api_v1_organizations__organization_id__controls__period__current_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                period: components["schemas"]["ControlPeriod"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ControlRecordUpsertRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ControlRecordResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_control_records_api_v1_organizations__organization_id__controls__period__records_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                period: components["schemas"]["ControlPeriod"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ControlRecordResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_control_record_api_v1_organizations__organization_id__control_records__record_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                record_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ControlRecordResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_control_record_api_v1_organizations__organization_id__control_records__record_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                record_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    edit_control_record_api_v1_organizations__organization_id__control_records__record_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                record_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ControlRecordUpsertRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ControlRecordResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_control_record_history_api_v1_organizations__organization_id__control_records__record_id__history_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                record_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ControlRecordHistoryResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_control_sheet_api_v1_organizations__organization_id__controls__period__sheet_get: {
        parameters: {
            query?: {
                /** @description YYYY-MM-DD. Defaults to the current period. */
                date?: string | null;
            };
            header?: never;
            path: {
                organization_id: string;
                period: components["schemas"]["ControlPeriod"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ControlSheetResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    check_control_item_api_v1_organizations__organization_id__controls__period__items__item_id__check_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                period: components["schemas"]["ControlPeriod"];
                item_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ItemCheckRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ControlSheetResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    submit_control_record_api_v1_organizations__organization_id__control_records__record_id__submit_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
                record_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ControlSheetResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_control_audit_events_api_v1_organizations__organization_id__control_records__record_id__audit_events_get: {
        parameters: {
            query?: {
                /** @description `next_cursor` from the previous page */
                cursor?: string | null;
                limit?: number;
            };
            header?: never;
            path: {
                organization_id: string;
                record_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuditEventPageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_dashboard_api_v1_organizations__organization_id__dashboard_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DashboardResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_setup_progress_api_v1_organizations__organization_id__setup_progress_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                organization_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SetupProgressResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
}

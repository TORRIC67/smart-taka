import FormCard from "../../components/FormCard.jsx";
import { binFields, customerFields, driverFields } from "../../fields.js";
import { post } from "../../api/client";
import { useI18n } from "../../useI18n";

// The admin registers customers, drivers (with their truck) and bins
export default function Register() {
  const { t } = useI18n();
  return (
    <>
      <FormCard
        title={t("register_customer_title")}
        fields={customerFields}
        withLocation
        submitLabel={t("register_customer_submit")}
        onSubmit={async (v) => t("register_customer_success", { id: (await post("/admin/customers", v)).id })}
      />
      <FormCard
        title={t("register_driver_title")}
        hint={t("register_driver_hint")}
        fields={driverFields}
        submitLabel={t("register_driver_submit")}
        onSubmit={async (v) => {
          const r = await post("/admin/drivers", v);
          return t("register_driver_success", { plate: r.plate_number });
        }}
      />
      <FormCard
        title={t("register_bin_title")}
        hint={t("register_bin_hint")}
        fields={binFields}
        withLocation
        submitLabel={t("register_bin_submit")}
        onSubmit={async (v) => t("register_bin_success", { code: (await post("/admin/bins", v)).code })}
      />
    </>
  );
}

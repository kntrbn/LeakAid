type Variant = "success" | "waiting" | "error";

const variantStyles: Record<Variant, string> = {
  success: "bg-green-50 text-green-700",
  waiting: "bg-gray-100 text-gray-600",
  error: "bg-red-50 text-red-600",
};

export function StatusBadge({
  variant,
  label,
}: {
  variant: Variant;
  label: string;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${variantStyles[variant]}`}
    >
      {label}
    </span>
  );
}

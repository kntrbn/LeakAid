type Props = {
  role: "agent" | "user";
  content: string;
};

export function ChatMessage({ role, content }: Props) {
  const isAgent = role === "agent";

  return (
    <div className={`flex ${isAgent ? "justify-start" : "justify-end"}`}>
      <div
        className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isAgent
            ? "rounded-bl-md bg-gray-200 text-gray-900"
            : "rounded-br-md bg-blue-600 text-white"
        }`}
      >
        {content}
      </div>
    </div>
  );
}

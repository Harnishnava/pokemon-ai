import Image from "next/image";
import Chat from "../components/Chat";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-100">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            Pokemon AI Assistant
          </h1>
          <p className="text-gray-600">Ask me anything about Pokemon!</p>
        </div>
        <Chat />
      </div>
    </div>
  );
}

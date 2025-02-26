// import { useState } from 'react';
// import { useImmer } from 'use-immer';
// import api from '@/api';
// import { parseSSEStream } from '@/utils';
// import ChatMessages from '@/components/ChatMessages';
// import ChatInput from '@/components/ChatInput';

// function Chatbot() {
//   const [chatId, setChatId] = useState(null);
//   const [messages, setMessages] = useImmer([]);
//   const [newMessage, setNewMessage] = useState('');

//   const isLoading = messages.length && messages[messages.length - 1].loading;

//   async function submitNewMessage() {
//     const trimmedMessage = newMessage.trim();
//     if (!trimmedMessage || isLoading) return;

//     setMessages(draft => [...draft,
//       { role: 'user', content: trimmedMessage },
//       { role: 'assistant', content: '', sources: [], loading: true }
//     ]);
//     setNewMessage('');

//     let chatIdOrNew = chatId;
//     try {
//       if (!chatId) {
//         const { id } = await api.createChat();
//         setChatId(id);
//         chatIdOrNew = id;
//       }

//       const stream = await api.sendChatMessage(chatIdOrNew, trimmedMessage);
//       for await (const textChunk of parseSSEStream(stream)) {
//         setMessages(draft => {
//           draft[draft.length - 1].content += textChunk;
//         });
//       }
//       setMessages(draft => {
//         draft[draft.length - 1].loading = false;
//       });
//     } catch (err) {
//       console.log(err);
//       setMessages(draft => {
//         draft[draft.length - 1].loading = false;
//         draft[draft.length - 1].error = true;
//       });
//     }
//   }

//   return (
//     <div className='relative grow flex flex-col gap-6 pt-6'>
//       {messages.length === 0 && (
//         <div className='mt-3 font-urbanist text-primary-blue text-xl font-light space-y-2'>
//           <p>👋 Welcome!</p>
//           <p>I am powered by the latest technology reports from leading institutions like the World Bank, the World Economic Forum, McKinsey, Deloitte and the OECD.</p>
//           <p>Ask me anything about the latest technology trends.</p>
//         </div>
//       )}
//       <ChatMessages
//         messages={messages}
//         isLoading={isLoading}
//       />
//       <ChatInput
//         newMessage={newMessage}
//         isLoading={isLoading}
//         setNewMessage={setNewMessage}
//         submitNewMessage={submitNewMessage}
//       />
//     </div>
//   );
// }

// export default Chatbot;
import { useState } from "react";
import { useImmer } from "use-immer";
import api from "@/api";
import { parseSSEStream } from "@/utils";
import ChatMessages from "@/components/ChatMessages";
import ChatInput from "@/components/ChatInput";

function Chatbot() {
  const [chatId, setChatId] = useState(null);
  const [messages, setMessages] = useImmer([]);
  const [newMessage, setNewMessage] = useState("");
  const [isCreatingNewChat, setIsCreatingNewChat] = useState(false);

  const isLoading = messages.length && messages[messages.length - 1].loading;

  async function submitNewMessage() {
    const trimmedMessage = newMessage.trim();
    if (!trimmedMessage || isLoading) return;

    setMessages((draft) => [
      ...draft,
      { role: "user", content: trimmedMessage },
      { role: "assistant", content: "", sources: [], loading: true },
    ]);
    setNewMessage("");

    let chatIdOrNew = chatId;
    try {
      if (!chatId) {
        const { id } = await api.createChat();
        setChatId(id);
        chatIdOrNew = id;
      }

      const stream = await api.sendChatMessage(chatIdOrNew, trimmedMessage);
      for await (const textChunk of parseSSEStream(stream)) {
        setMessages((draft) => {
          draft[draft.length - 1].content += textChunk;
        });
      }

      setMessages((draft) => {
        draft[draft.length - 1].loading = false;
      });
    } catch (err) {
      console.log(err);
      setMessages((draft) => {
        draft[draft.length - 1].loading = false;
        draft[draft.length - 1].error = true;
      });
    }
  }

  // Function to start a new chat
  async function startNewChat() {
    setIsCreatingNewChat(true);
    setMessages([]); // Clear the previous messages
    setChatId(null); // Reset chat ID

    try {
      const { id } = await api.createChat(); // Request a new chat ID
      setChatId(id);
    } catch (err) {
      console.error("Error creating new chat:", err);
    } finally {
      setIsCreatingNewChat(false);
    }
  }

  return (
    <div className="relative grow flex flex-col gap-6 pt-6">
      {/* Just the main title at the top */}
      <div className="text-center mb-4">
        <h1 className="text-2xl font-bold text-primary-blue">
          CrewCoder AI Chat
        </h1>
      </div>

      {messages.length === 0 && (
        <div className="mt-3 font-urbanist text-primary-blue text-xl font-light space-y-2">
          <p>👋 Welcome!</p>
          <p>
            I am powered by the latest technology reports from leading
            institutions.
          </p>
          <p>Ask me anything about the latest technology trends.</p>
        </div>
      )}

      <ChatMessages messages={messages} isLoading={isLoading} />

      {/* Input area with New Chat button to the left */}
      <div className="flex items-center gap-3">
        {/* New Chat button to the left of input with fully rounded corners */}
        <button
          onClick={startNewChat}
          disabled={isCreatingNewChat}
          className="flex-shrink-0 flex items-center gap-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-full transition-all duration-200 shadow-sm hover:shadow-md focus:outline-none focus:ring-2 focus:ring-blue-300"
        >
          <span>{isCreatingNewChat ? "⏳" : "🔄"}</span>
          <span className="whitespace-nowrap">
            {isCreatingNewChat ? "Starting..." : "New Chat"}
          </span>
        </button>

        {/* Chat input takes remaining space */}
        <div className="flex-grow">
          <ChatInput
            newMessage={newMessage}
            isLoading={isLoading}
            setNewMessage={setNewMessage}
            submitNewMessage={submitNewMessage}
          />
        </div>
      </div>
    </div>
  );
}

export default Chatbot;

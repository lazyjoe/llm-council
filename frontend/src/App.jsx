import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import { api } from './api';
import './App.css';

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Load conversation details when selected
  useEffect(() => {
    if (currentConversationId) {
      loadConversation(currentConversationId);
    }
  }, [currentConversationId]);

  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const handleNewConversation = async () => {
    try {
      const newConv = await api.createConversation();
      setConversations([
        { id: newConv.id, created_at: newConv.created_at, message_count: 0 },
        ...conversations,
      ]);
      setCurrentConversationId(newConv.id);
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const handleSelectConversation = (id) => {
    setCurrentConversationId(id);
    setIsSidebarOpen(false); // Close sidebar on mobile when selecting conversation
  };

  const handleDeleteConversation = async (id) => {
    try {
      await api.deleteConversation(id);

      // Remove from conversations list
      setConversations(conversations.filter(conv => conv.id !== id));

      // If the deleted conversation was currently selected, clear it
      if (currentConversationId === id) {
        setCurrentConversationId(null);
        setCurrentConversation(null);

        // Optionally, select the first available conversation
        const remainingConversations = conversations.filter(conv => conv.id !== id);
        if (remainingConversations.length > 0) {
          setCurrentConversationId(remainingConversations[0].id);
        }
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      alert('Failed to delete conversation. Please try again.');
    }
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const closeSidebar = () => {
    setIsSidebarOpen(false);
  };

  const handleRetryStage2 = async (messageIndex) => {
    if (!currentConversationId) return;

    setCurrentConversation((prev) => {
      const messages = [...prev.messages];
      messages[messageIndex] = {
        ...messages[messageIndex],
        retrying: true,
        loading: { stage1: false, stage2: true, stage3: false },
      };
      return { ...prev, messages };
    });

    try {
      await api.retryStage2Stream(currentConversationId, (eventType, event) => {
        switch (eventType) {
          case 'stage2_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              messages[messageIndex] = {
                ...messages[messageIndex],
                stage2: event.data,
                metadata: event.metadata,
                loading: { ...messages[messageIndex].loading, stage2: false, stage3: true },
              };
              return { ...prev, messages };
            });
            break;

          case 'stage3_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              messages[messageIndex] = {
                ...messages[messageIndex],
                stage3: event.data,
                retrying: false,
                loading: { stage1: false, stage2: false, stage3: false },
              };
              return { ...prev, messages };
            });
            break;

          case 'complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              messages[messageIndex] = {
                ...messages[messageIndex],
                retrying: false,
                loading: { stage1: false, stage2: false, stage3: false },
              };
              return { ...prev, messages };
            });
            break;

          case 'error':
            console.error('Retry Stage 2 error:', event.message);
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              messages[messageIndex] = {
                ...messages[messageIndex],
                retrying: false,
                loading: { stage1: false, stage2: false, stage3: false },
              };
              return { ...prev, messages };
            });
            break;
        }
      });
    } catch (error) {
      console.error('Failed to retry Stage 2:', error);
      setCurrentConversation((prev) => {
        const messages = [...prev.messages];
        messages[messageIndex] = {
          ...messages[messageIndex],
          retrying: false,
          loading: { stage1: false, stage2: false, stage3: false },
        };
        return { ...prev, messages };
      });
    }
  };

  const handleRetryStage3 = async (messageIndex) => {
    if (!currentConversationId) return;

    setCurrentConversation((prev) => {
      const messages = [...prev.messages];
      messages[messageIndex] = {
        ...messages[messageIndex],
        retrying: true,
        loading: { stage1: false, stage2: false, stage3: true },
      };
      return { ...prev, messages };
    });

    try {
      await api.retryStage3Stream(currentConversationId, (eventType, event) => {
        switch (eventType) {
          case 'stage3_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              messages[messageIndex] = {
                ...messages[messageIndex],
                stage3: event.data,
                retrying: false,
                loading: { stage1: false, stage2: false, stage3: false },
              };
              return { ...prev, messages };
            });
            break;

          case 'complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              messages[messageIndex] = {
                ...messages[messageIndex],
                retrying: false,
                loading: { stage1: false, stage2: false, stage3: false },
              };
              return { ...prev, messages };
            });
            break;

          case 'error':
            console.error('Retry Stage 3 error:', event.message);
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              messages[messageIndex] = {
                ...messages[messageIndex],
                retrying: false,
                loading: { stage1: false, stage2: false, stage3: false },
              };
              return { ...prev, messages };
            });
            break;
        }
      });
    } catch (error) {
      console.error('Failed to retry Stage 3:', error);
      setCurrentConversation((prev) => {
        const messages = [...prev.messages];
        messages[messageIndex] = {
          ...messages[messageIndex],
          retrying: false,
          loading: { stage1: false, stage2: false, stage3: false },
        };
        return { ...prev, messages };
      });
    }
  };

  const handleSendMessage = async (content) => {
    if (!currentConversationId) return;

    setIsLoading(true);
    try {
      // Optimistically add user message to UI
      const userMessage = { role: 'user', content };
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
      }));

      // Create a partial assistant message that will be updated progressively
      const assistantMessage = {
        role: 'assistant',
        stage1: null,
        stage2: null,
        stage3: null,
        metadata: null,
        loading: {
          stage1: false,
          stage2: false,
          stage3: false,
        },
      };

      // Add the partial assistant message
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
      }));

      // Send message with streaming
      await api.sendMessageStream(currentConversationId, content, (eventType, event) => {
        switch (eventType) {
          case 'stage1_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = { ...messages[messages.length - 1] };
              lastMsg.loading = { ...lastMsg.loading, stage1: true };
              messages[messages.length - 1] = lastMsg;
              return { ...prev, messages };
            });
            break;

          case 'stage1_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = { ...messages[messages.length - 1] };
              lastMsg.stage1 = event.data;
              lastMsg.loading = { ...lastMsg.loading, stage1: false };
              messages[messages.length - 1] = lastMsg;
              return { ...prev, messages };
            });
            break;

          case 'stage2_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = { ...messages[messages.length - 1] };
              lastMsg.loading = { ...lastMsg.loading, stage2: true };
              messages[messages.length - 1] = lastMsg;
              return { ...prev, messages };
            });
            break;

          case 'stage2_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = { ...messages[messages.length - 1] };
              lastMsg.stage2 = event.data;
              lastMsg.metadata = event.metadata;
              lastMsg.loading = { ...lastMsg.loading, stage2: false };
              messages[messages.length - 1] = lastMsg;
              return { ...prev, messages };
            });
            break;

          case 'stage3_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = { ...messages[messages.length - 1] };
              lastMsg.loading = { ...lastMsg.loading, stage3: true };
              messages[messages.length - 1] = lastMsg;
              return { ...prev, messages };
            });
            break;

          case 'stage3_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = { ...messages[messages.length - 1] };
              lastMsg.stage3 = event.data;
              lastMsg.loading = { ...lastMsg.loading, stage3: false };
              messages[messages.length - 1] = lastMsg;
              return { ...prev, messages };
            });
            break;

          case 'title_complete':
            // Reload conversations to get updated title
            loadConversations();
            break;

          case 'complete':
            // Stream complete, reload conversations list
            loadConversations();
            setIsLoading(false);
            break;

          case 'error':
            console.error('Stream error:', event.message);
            setIsLoading(false);
            break;

          default:
            console.log('Unknown event type:', eventType);
        }
      });

      // Ensure loading is stopped even if 'complete' event wasn't received
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove optimistic messages on error
      setCurrentConversation((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -2),
      }));
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      {/* Mobile hamburger button */}
      <button
        className="mobile-menu-btn"
        onClick={toggleSidebar}
        aria-label="Toggle menu"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="3" y1="12" x2="21" y2="12"></line>
          <line x1="3" y1="6" x2="21" y2="6"></line>
          <line x1="3" y1="18" x2="21" y2="18"></line>
        </svg>
      </button>

      {/* Backdrop for mobile */}
      {isSidebarOpen && <div className="sidebar-backdrop" onClick={closeSidebar}></div>}

      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        isOpen={isSidebarOpen}
        onClose={closeSidebar}
      />
      <ChatInterface
        conversation={currentConversation}
        onSendMessage={handleSendMessage}
        onRetryStage2={handleRetryStage2}
        onRetryStage3={handleRetryStage3}
        isLoading={isLoading}
      />
    </div>
  );
}

export default App;

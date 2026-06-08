import { render, screen } from '@testing-library/react';
import MessageList from './MessageList';

const messages = [
  { sender: 'AI Chatbot', content: 'Hello!' },
  { sender: 'You', content: 'Hi there' },
];

const avatar = { image_url: null };

describe('MessageList', () => {
  it('renders all messages', () => {
    render(<MessageList messages={messages} isTyping={false} avatar={avatar} />);
    expect(screen.getByText('Hello!')).toBeInTheDocument();
    expect(screen.getByText('Hi there')).toBeInTheDocument();
  });

  it('renders empty list without crashing', () => {
    const { container } = render(
      <MessageList messages={[]} isTyping={false} avatar={avatar} />
    );
    expect(container.querySelector('.messages-box')).toBeInTheDocument();
  });

  it('shows typing indicator when isTyping is true', () => {
    const { container } = render(
      <MessageList messages={messages} isTyping={true} avatar={avatar} />
    );
    expect(container.querySelector('.typing-indicator')).toBeInTheDocument();
  });

  it('hides typing indicator when isTyping is false', () => {
    const { container } = render(
      <MessageList messages={messages} isTyping={false} avatar={avatar} />
    );
    expect(container.querySelector('.typing-indicator')).not.toBeInTheDocument();
  });
});

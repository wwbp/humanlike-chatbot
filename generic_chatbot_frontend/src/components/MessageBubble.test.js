import { render, screen } from '@testing-library/react';
import MessageBubble from './MessageBubble';

describe('MessageBubble', () => {
  const avatar = { image_url: 'http://example.com/avatar.png' };

  it('applies sent class for user messages', () => {
    const { container } = render(
      <MessageBubble sender="You" content="Hello" avatar={avatar} />
    );
    expect(container.querySelector('.message-row.sent')).toBeTruthy();
    expect(container.querySelector('.message.sent')).toBeTruthy();
  });

  it('applies received class for bot messages', () => {
    const { container } = render(
      <MessageBubble sender="AI Chatbot" content="Hi there" avatar={avatar} />
    );
    expect(container.querySelector('.message-row.received')).toBeTruthy();
    expect(container.querySelector('.message.received')).toBeTruthy();
  });

  it('shows avatar image for bot messages when image_url is set', () => {
    render(
      <MessageBubble sender="AI Chatbot" content="Hi" avatar={avatar} />
    );
    const img = screen.getByAltText('Avatar');
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('src', avatar.image_url);
  });

  it('does not show avatar for user messages', () => {
    render(
      <MessageBubble sender="You" content="Hello" avatar={avatar} />
    );
    expect(screen.queryByAltText('Avatar')).not.toBeInTheDocument();
  });

  it('does not show avatar when image_url is null', () => {
    render(
      <MessageBubble sender="AI Chatbot" content="Hi" avatar={{ image_url: null }} />
    );
    expect(screen.queryByAltText('Avatar')).not.toBeInTheDocument();
  });

  it('renders message content', () => {
    render(
      <MessageBubble sender="You" content="Test message" avatar={{}} />
    );
    expect(screen.getByText('Test message')).toBeInTheDocument();
  });
});

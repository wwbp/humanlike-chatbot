import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Simulate from './Simulate';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

const fillForm = (overrides = {}) => {
  const defaults = {
    botName: 'my-bot',
    conversationId: 'conv-1',
    participantId: 'p-1',
    studyName: 'study-a',
    userGroup: 'group-a',
  };
  const vals = { ...defaults, ...overrides };

  fireEvent.change(screen.getByLabelText(/bot name/i), {
    target: { value: vals.botName },
  });
  fireEvent.change(screen.getByLabelText(/conversation id/i), {
    target: { value: vals.conversationId },
  });
  fireEvent.change(screen.getByLabelText(/participant id/i), {
    target: { value: vals.participantId },
  });
  fireEvent.change(screen.getByLabelText(/study name/i), {
    target: { value: vals.studyName },
  });
  fireEvent.change(screen.getByLabelText(/user group/i), {
    target: { value: vals.userGroup },
  });
};

const renderSimulate = () =>
  render(
    <MemoryRouter>
      <Simulate />
    </MemoryRouter>
  );

const mockAlert = vi.fn();

beforeEach(() => {
  mockNavigate.mockClear();
  mockAlert.mockClear();
  vi.stubGlobal('alert', mockAlert);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('Simulate', () => {
  it('renders all form fields and submit button', () => {
    renderSimulate();
    expect(screen.getByLabelText(/bot name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/conversation id/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/participant id/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/study name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/user group/i)).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /start conversation/i })
    ).toBeInTheDocument();
  });

  it('shows alert and does not navigate when fields are empty', () => {
    renderSimulate();
    // Use fireEvent.submit to bypass HTML5 required-field validation in jsdom
    fireEvent.submit(document.querySelector('form'));
    expect(mockAlert).toHaveBeenCalled();
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('navigates to /conversation for a regular bot name', () => {
    renderSimulate();
    fillForm({ botName: 'my-bot' });
    fireEvent.click(
      screen.getByRole('button', { name: /start conversation/i })
    );
    expect(mockNavigate).toHaveBeenCalledOnce();
    const [path] = mockNavigate.mock.calls[0];
    expect(path).toMatch(/^\/conversation\?/);
  });

  it('navigates to /voice-conversation when bot name contains -voice', () => {
    renderSimulate();
    fillForm({ botName: 'my-bot-voice' });
    fireEvent.click(
      screen.getByRole('button', { name: /start conversation/i })
    );
    const [path] = mockNavigate.mock.calls[0];
    expect(path).toMatch(/^\/voice-conversation\?/);
  });

  it('includes all params in the navigation URL', () => {
    renderSimulate();
    fillForm({
      botName: 'test-bot',
      conversationId: 'conv-123',
      participantId: 'p-456',
      studyName: 'my-study',
      userGroup: 'control',
    });
    fireEvent.click(
      screen.getByRole('button', { name: /start conversation/i })
    );
    const [path] = mockNavigate.mock.calls[0];
    const qs = path.split('?')[1];
    const params = new URLSearchParams(qs);
    expect(params.get('bot_name')).toBe('test-bot');
    expect(params.get('conversation_id')).toBe('conv-123');
    expect(params.get('participant_id')).toBe('p-456');
    expect(params.get('study_name')).toBe('my-study');
    expect(params.get('user_group')).toBe('control');
  });
});

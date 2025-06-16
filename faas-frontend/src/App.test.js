import { render, screen } from '@testing-library/react';
import App from './App';

test('renders FaaS Portal title', () => {
  render(<App />);
  const titleElement = screen.getByText(/FaaS Portal/i);
  expect(titleElement).toBeInTheDocument();
});
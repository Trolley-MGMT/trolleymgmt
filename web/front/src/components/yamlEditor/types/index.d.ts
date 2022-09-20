/* eslint-disable no-unused-vars */
/// <reference types="react" />
interface EditorProps {
  json?: {};
  text?: string;
  onChange?: (value: { json: {}; text: string }) => void;
  onError?: (error: {}) => void;
  theme?: any;
}
declare const YamlEditor: (props: EditorProps) => JSX.Element;
export default YamlEditor;

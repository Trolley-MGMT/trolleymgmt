import React from 'react';
import yaml from 'js-yaml';

import YamlInput from './YamlInput';

const useErrors = (onError) => {
  const [error, setError] = React.useState(null);

  const cleanErrors = () => setError(null);

  const markError = ({ position, message, snippet }) => {
    setError({ position, message, snippet });
    onError(true);
  };

  return {
    cleanErrors,
    errorRanges: error,
    markError,
    hasErrors: !!error,
    error,
  };
};

const defaultMerge = ({ text, currentText }) => {
  if (!currentText) {
    return {
      text,
    };
  }
  return {
    text: currentText,
  };
};

const getMergedValue = ({ merge, json, text, currentText }) => {
  if (!text && !currentText && !json) {
    return '';
  }
  if (!text && !json) {
    return currentText;
  }
  const shouldUpdate = merge({ json, text, currentText });

  if (
    shouldUpdate.text !== undefined &&
    typeof shouldUpdate.text === 'string'
  ) {
    return shouldUpdate.text;
  }
  if (shouldUpdate.json) {
    return yaml.dump(shouldUpdate.json);
  }
  throw new Error(
    'merge function should return object with "text" or "json" fields',
  );
};

const YamlEditor = (
  {
    json,
    text,
    theme,
    onError = () => {},
    onChange = () => {},
    onSelect = () => {},
    onSetCursor = () => {},
    merge = defaultMerge,
  },
  ref,
) => {
  const actionsRef = React.useRef(null);
  const errors = useErrors(onError);
  const textValue = json ? yaml.dump(json) : text;
  const currentText = React.useRef(textValue);

  const replaceValue = (val) => {
    if (!val.json && !val.text) {
      return;
    }
    const newText = val.json ? yaml.dump(val.json) : val.text;
    actionsRef.current.actionNewDoc({ text: newText });
  };

  const mergedValue = React.useMemo(
    () =>
      getMergedValue({
        merge,
        json,
        text,
        currentText: currentText.current,
      }),
    [json, text, merge],
  );

  React.useEffect(() => {
    if (mergedValue !== currentText.current) {
      replaceValue({ text: mergedValue });
    }
  }, [mergedValue]);

  const handleChange = (newText) => {
    try {
      currentText.current = newText;
      const newJson = yaml.load(newText);
      if (errors.hasErrors) {
        errors.cleanErrors();
        onError(null);
      }

      onChange({ json: newJson, text: newText });
    } catch (err) {
      onError(err);
      if (!err.mark?.snippet) {
        console.error(err);
        return;
      }
      console.error(err.mark.snippet);
      errors.markError({
        position: err.mark.position,
        message: err.message,
        snippet: err.mark.snippet,
      });
    }
  };

  const actions = {
    replaceValue,
  };

  if (ref) {
    // eslint-disable-next-line no-param-reassign
    ref.current = actions;
  }

  const handleSelect = (selected) => {
    onSelect(selected);
  };

  const handleSetCursor = (underCursor) => {
    onSetCursor(underCursor);
  };

  const getErrorPos = (newText) => {
    try {
      yaml.load(newText);
      return {};
    } catch (err) {
      if (!err.mark?.snippet) {
        return {};
      }
      return { position: err.mark.position };
    }
  };

  return (
    <YamlInput
      value={mergedValue}
      onChange={handleChange}
      onSelect={handleSelect}
      onSetCursor={handleSetCursor}
      error={errors.error}
      getErrorPos={getErrorPos}
      options={{ handleTabs: true, theme }}
      ref={actionsRef}
    />
  );
};

export default React.forwardRef(YamlEditor);

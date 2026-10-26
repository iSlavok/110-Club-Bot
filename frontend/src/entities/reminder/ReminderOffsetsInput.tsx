import {
  ActionIcon,
  Button,
  Group,
  MultiSelect,
  NumberInput,
  Pill,
  Select,
  Stack,
} from '@mantine/core';
import { IconEye } from '@tabler/icons-react';
import { useState, type ReactNode } from 'react';

import {
  formatOffset,
  latestFirst,
  MAX_OFFSET_MINUTES,
  MAX_OFFSETS,
  OFFSET_PRESETS,
  OFFSET_UNITS,
  type OffsetUnit,
} from './offsets';

interface ReminderOffsetsInputProps {
  label: string;
  value: number[];
  onChange: (value: number[]) => void;
  /** How the zero offset reads: «в момент начала», «в дедлайн». */
  zeroLabel?: string;
  disabled?: boolean;
  error?: ReactNode;
  /** Adds an eye button to every chosen offset. */
  onPreview?: (offset: number) => void;
}

export function ReminderOffsetsInput({
  label,
  value,
  onChange,
  zeroLabel,
  disabled = false,
  error,
  onPreview,
}: ReminderOffsetsInputProps) {
  const [amount, setAmount] = useState<number | string>('');
  const [unit, setUnit] = useState<OffsetUnit>('hours');
  const unitMinutes = OFFSET_UNITS.find((option) => option.value === unit)?.minutes ?? 1;
  const custom = typeof amount === 'number' ? amount * unitMinutes : null;
  const canAdd =
    custom !== null &&
    custom >= 1 &&
    custom <= MAX_OFFSET_MINUTES &&
    !value.includes(custom) &&
    value.length < MAX_OFFSETS;
  const options = latestFirst([...OFFSET_PRESETS, ...value]).map((minutes) => ({
    value: String(minutes),
    label: formatOffset(minutes, zeroLabel),
  }));

  return (
    <Stack gap={6}>
      <MultiSelect
        label={label}
        data={options}
        value={value.map(String)}
        onChange={(selected) => {
          onChange(latestFirst(selected.map(Number)));
        }}
        maxValues={MAX_OFFSETS}
        disabled={disabled}
        error={error}
        clearable
        renderPill={
          onPreview &&
          (({ option, value: offset, onRemove }) => (
            <Pill withRemoveButton={!disabled} onRemove={onRemove}>
              <Group gap={4} wrap="nowrap" component="span">
                <ActionIcon
                  size={16}
                  variant="transparent"
                  aria-label={`${label}: текст «${option.label}»`}
                  // The pill sits inside the select: without this the press also opens its dropdown.
                  onMouseDown={(event) => {
                    event.preventDefault();
                    event.stopPropagation();
                  }}
                  onClick={(event) => {
                    event.stopPropagation();
                    onPreview(Number(offset));
                  }}
                >
                  <IconEye size={14} />
                </ActionIcon>
                {option.label}
              </Group>
            </Pill>
          ))
        }
      />
      {!disabled && (
        <Group gap="xs" align="flex-end">
          <NumberInput
            aria-label={`${label}: своё значение`}
            placeholder="Своё"
            w={110}
            min={1}
            allowDecimal={false}
            allowNegative={false}
            value={amount}
            onChange={setAmount}
          />
          <Select
            aria-label={`${label}: единица`}
            w={110}
            data={OFFSET_UNITS.map((option) => ({ value: option.value, label: option.label }))}
            value={unit}
            allowDeselect={false}
            onChange={(selected) => {
              const option = OFFSET_UNITS.find((candidate) => candidate.value === selected);
              if (option) {
                setUnit(option.value);
              }
            }}
          />
          <Button
            variant="default"
            aria-label={`${label}: добавить`}
            disabled={!canAdd}
            onClick={() => {
              if (custom !== null) {
                onChange(latestFirst([...value, custom]));
                setAmount('');
              }
            }}
          >
            Добавить
          </Button>
        </Group>
      )}
    </Stack>
  );
}

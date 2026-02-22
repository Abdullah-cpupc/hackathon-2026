declare module 'react-color' {
  export interface ColorResult {
    hex: string;
  }
  export interface BlockPickerProps {
    color?: string;
    colors?: string[];
    onChangeComplete?: (color: ColorResult) => void;
    width?: string;
    triangle?: 'hide' | 'top-left' | 'top-right' | string;
  }
  export const BlockPicker: React.ComponentType<BlockPickerProps>;
  export interface TwitterPickerProps {
    color?: string;
    colors?: string[];
    triangle?: 'hide' | 'top-left' | 'top-right';
    onChangeComplete?: (color: ColorResult) => void;
  }
  export const TwitterPicker: React.ComponentType<TwitterPickerProps>;
}

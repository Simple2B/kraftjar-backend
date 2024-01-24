import {Modal} from 'flowbite';
import type {ModalOptions, ModalInterface} from 'flowbite';

// /*
//  * $editFieldModal: required
//  * options: optional
//  */

// // For your js code

interface IField {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  is_deleted: boolean;
}

const $modalElement: HTMLElement = document.querySelector('#editFieldModal');
const $addFieldModalElement: HTMLElement =
  document.querySelector('#add-field-modal');

const modalOptions: ModalOptions = {
  placement: 'bottom-right',
  backdrop: 'dynamic',
  backdropClasses:
    'bg-gray-900 bg-opacity-50 dark:bg-opacity-80 fixed inset-0 z-40',
  closable: true,
  onHide: () => {
    console.log('modal is hidden');
  },
  onShow: () => {
    console.log('field id: ');
  },
  onToggle: () => {
    console.log('modal has been toggled');
  },
};

const modal: ModalInterface = new Modal($modalElement, modalOptions);
const addModal: ModalInterface = new Modal($addFieldModalElement, modalOptions);

const $buttonElements = document.querySelectorAll('.field-edit-button');
$buttonElements.forEach(e =>
  e.addEventListener('click', () => {
    editField(JSON.parse(e.getAttribute('data-target')));
  }),
);


// closing add field modal
const addModalCloseBtn = document.querySelector('#modalAddCloseButton');
if (addModalCloseBtn) {
  addModalCloseBtn.addEventListener('click', () => {
    addModal.hide();
  });
}

// search flow
const searchInput: HTMLInputElement = document.querySelector(
  '#table-search-fields',
);
const searchInputButton = document.querySelector('#table-search-field-button');
if (searchInputButton && searchInput) {
  searchInputButton.addEventListener('click', () => {
    const url = new URL(window.location.href);
    url.searchParams.set('q', searchInput.value);
    window.location.href = `${url.href}`;
  });
}
const deleteButtons = document.querySelectorAll('.delete-field-btn');

deleteButtons.forEach(e => {
  e.addEventListener('click', async () => {
    if (confirm('Are sure?')) {
      let id = e.getAttribute('data-field-id');
      const response = await fetch(`/field/delete/${id}`, {
        method: 'DELETE',
      });
      if (response.status == 200) {
        location.reload();
      }
    }
  });
});

function editField(field: IField) {
  let input: HTMLInputElement = document.querySelector('#field-edit-first-name');
  input.value = field.first_name;
  input = document.querySelector('#field-edit-last-name');
  input.value = field.last_name;
  input = document.querySelector('#field-edit-id');
  input.value = field.id.toString();
  input = document.querySelector('#field-edit-phone');
  input.value = field.phone;
  input = document.querySelector('#field-edit-email');
  input.value = field.email;
  input = document.querySelector('#field-edit-password');
  input.value = '*******';
  input = document.querySelector('#field-edit-password_confirmation');
  input.value = '*******';
  input = document.querySelector('#field-edit-is-deleted');
  input.checked = field.is_deleted;
  input = document.querySelector('#field-edit-next_url');
  input.value = window.location.href;
  modal.show();
}

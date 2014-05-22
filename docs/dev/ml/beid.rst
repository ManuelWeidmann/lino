BeId - read Belgian eId cards
=============================

.. module:: ml.beid

.. class:: BeIdCardTypes

    List of Belgian Identification Card Types.
    
    Didn't yet find any official reference document.
    
    The eID applet returns a field `documentType` which contains a
    numeric code.  For example 1 is for "Belgian citizen", 6 for "Kids
    card",...
    
    The eID viewer, when saving a card as xml file, doesn't save these
    values nowhere, it saves a string equivalent (1 becomes
    "belgian_citizen", 6 becomes "kids_card", 17 becomes
    "foreigner_f", 16 becomes "foreigner_e_plus",...
    
    Sources:
    | [1] https://securehomes.esat.kuleuven.be/~decockd/wiki/bin/view.cgi/EidForums/ForumEidCards0073
    | [2] `Enum be.fedict.commons.eid.consumer.DocumentType <http://code.google.com/p/eid-applet/source/browse/trunk/eid-applet-service/src/main/java/be/fedict/eid/applet/service/DocumentType.java>`_


    Excerpts from [1]: 
    
    - Johan: A document type of 7 is used for bootstrap cards ? What
      is a bootstrap card (maybe some kind of test card?)  Danny: A
      bootstrap card was an eID card that was used in the early start
      of the eID card introduction to bootstrap the computers at the
      administration. This type is no longer issued.
    
    - Johan: A document type of 8 is used for a
      "habilitation/machtigings" card ? Is this for refugees or asylum
      seekers? Danny: A habilitation/machtigings card was aimed at
      civil servants. This type is also no longer used.
    




.. class:: BeIdCardHolder

    Mixin for models which represent an eid card holder.
    Currently only Belgian eid cards are tested.
    Concrete subclasses must also inherit from :mod:`lino.mixins.Born`.

.. class:: BaseBeIdReadCardAction

  Common base for all "Read eID card" actions.

  .. method:: card2client(self, data)

     Does the actual conversion of the data fields coming from the card into database fields to be stored in the CardH


.. class:: FindByBeIdAction(BaseBeIdReadCardAction)

    Read an eID card without being on a holder. Either show the holder
    or ask to create a new holder.

    This is a list action, usually called from a quicklink or a main
    menu item.



.. class:: BeIdReadCardAction

  Read eId card and store the data on the selected holder.

  This is a row action (called on a given holder).

  - When the selected holder has an empty `national_id`, and when
    there is no holder yet with that `national_id` in the database,
    then we want to update the existing holder from the card.

